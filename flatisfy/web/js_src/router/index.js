import Vue from 'vue'
import VueRouter from 'vue-router'

import Home from '../views/home.vue'
import Status from '../views/status.vue'
import Details from '../views/details.vue'

Vue.use(VueRouter)

export default new VueRouter({
    routes: [
      { path: '/', component: Home, name: 'home' },
      { path: '/new', redirect: '/' },
      { path: '/followed', component: Status, name: 'followed' },
      { path: '/ignored', component: Status, name: 'ignored' },
      { path: '/user_deleted', component: Status, name: 'user_deleted' },
      { path: '/flat/:id', component: Details, name: 'details' }
    ]
})
