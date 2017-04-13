import Vue from 'vue'

import * as types from './mutations-types'

export const state = {
    flats: [],
    timeToPlaces: []
}

export const mutations = {
    [types.REPLACE_FLATS] (state, { flats }) {
        state.flats = flats
    },
    [types.MERGE_FLATS] (state, { flats }) {
        flats.forEach(flat => {
            const flatIndex = state.flats.findIndex(storedFlat => storedFlat.id === flat.id)

            if (flatIndex > -1) {
                Vue.set(state.flats, flatIndex, flat)
            } else {
                state.flats.push(flat)
            }
        })
    },
    [types.UPDATE_FLAT_STATUS] (state, { flatId, newStatus }) {
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'status', newStatus)
        }
    },
    [types.RECEIVE_TIME_TO_PLACES] (state, { timeToPlaces }) {
        state.timeToPlaces = timeToPlaces
    }
}
