import Vue from 'vue'
import VueRouter from 'vue-router'

import Home from '../views/home.vue'
import Status from '../views/status.vue'
import Details from '../views/details.vue'
import Search from '../views/search.vue'

Vue.use(VueRouter)

export default new VueRouter({
    routes: [
      { path: '/', component: Home, name: 'home' },
      { path: '/new', redirect: '/' },
      { path: '/status/:status', component: Status, name: 'status' },
      { path: '/flat/:id', component: Details, name: 'details' },
      { path: '/search', component: Search, name: 'search' }
    ]
})
