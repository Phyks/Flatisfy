import Vue from 'vue'

import i18n from './i18n'
import router from './router'
import store from './store'
import { costFilter } from './tools'

import App from './components/app.vue'

Vue.filter('cost', costFilter)

new Vue({
    i18n,
    router,
    store,
    render: createEle => createEle(App)
}).$mount('#app')
