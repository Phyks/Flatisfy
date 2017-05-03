import Vue from 'vue'

import * as types from './mutations-types'

export const state = {
    flats: [],
    timeToPlaces: [],
    loading: false
}

export const mutations = {
    [types.REPLACE_FLATS] (state, { flats }) {
        state.loading = false
        state.flats = flats
    },
    [types.MERGE_FLATS] (state, { flats }) {
        state.loading = false
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
        state.loading = false
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'status', newStatus)
        }
    },
    [types.UPDATE_FLAT_NOTES] (state, { flatId, newNotes }) {
        state.loading = false
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'notes', newNotes)
        }
    },
    [types.UPDATE_FLAT_NOTATION] (state, { flatId, newNotation }) {
        state.loading = false
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'notation', newNotation)
        }
    },
    [types.RECEIVE_TIME_TO_PLACES] (state, { timeToPlaces }) {
        state.loading = false
        state.timeToPlaces = timeToPlaces
    },
    [types.IS_LOADING] (state) {
        state.loading = true
    }
}
