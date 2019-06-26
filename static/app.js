const vm = new Vue({
  el: '#app',
  data: {
    trends: [],
    trendsNameArray: [],
    ws: new ReconnectingWebSocket(location.protocol.replace("http", "ws") + "//" + location.host + "/ws"),
    isActive: false
  },
  delimiters: ["<%","%>"],
  mounted: function() {
    this.ws.onopen = () => {
      console.log("open")
    }

    this.ws.onmessage = (evt) => {
      this.flashTwitterLogo()
      this.trendsNameArray = this.trends.map(value => value.name)
      this.trends.splice(0, this.trends.length)
      this.trends = this.trends.concat(JSON.parse(evt.data))
    }
  },

  computed: {
    upTo25: function() {
      return this.trends.slice(0, 25)
    },
    upTo50: function() {
      return this.trends.slice(25, 50)
    }
  },

  methods: {
    flashTwitterLogo: function() {
      const sleep = msec => new Promise(resolve => setTimeout(resolve, msec))
      const asyncfunc = async () => {
        this.isActive = true
        await sleep(1000)
        this.isActive = false
      }
      asyncfunc()
    },

    isNew: function (name) {
      if (this.trendsNameArray.length === 0) {
        return null
      }
      return this.trendsNameArray.some(v => v === name) ? null : "new" 
    }
  }

})