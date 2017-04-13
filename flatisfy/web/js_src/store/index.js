import Vue from 'vue'
import Vuex from 'vuex'

import actions from './actions'
import getters from './getters'
import { state, mutations } from './mutations'
// import products from './modules/products'

Vue.use(Vuex)

export default new Vuex.Store({
    state,
    actions,
    getters,
    mutations
})
