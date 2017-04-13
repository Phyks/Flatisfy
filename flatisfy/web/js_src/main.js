import Vue from 'vue'

import i18n from './i18n'
import router from './router'
import store from './store'

import App from './components/app.vue'

new Vue({
    i18n,
    router,
    store,
    render: createEle => createEle(App)
}).$mount('#app')
