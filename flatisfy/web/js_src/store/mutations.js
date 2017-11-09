import Vue from 'vue'

import * as types from './mutations-types'

export const state = {
    flats: [],
    timeToPlaces: [],
    loading: 0
}

export const mutations = {
    [types.REPLACE_FLATS] (state, { flats }) {
        state.flats = flats
        state.loading -= 1
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
        state.loading = false
        state.loading -= 1
    },
    [types.UPDATE_FLAT_STATUS] (state, { flatId, newStatus }) {
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'status', newStatus)
        }
        state.loading -= 1
    },
    [types.UPDATE_FLAT_NOTES] (state, { flatId, newNotes }) {
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'notes', newNotes)
        }
        state.loading -= 1
    },
    [types.UPDATE_FLAT_NOTATION] (state, { flatId, newNotation }) {
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'notation', newNotation)
        }
        state.loading -= 1
    },
    [types.UPDATE_FLAT_VISIT_DATE] (state, { flatId, newVisitDate }) {
        const index = state.flats.findIndex(flat => flat.id === flatId)
        if (index > -1) {
            Vue.set(state.flats[index], 'visit-date', newVisitDate)
        }
        state.loading -= 1
    },
    [types.RECEIVE_TIME_TO_PLACES] (state, { timeToPlaces }) {
        state.timeToPlaces = timeToPlaces
        state.loading -= 1
    },
    [types.IS_LOADING] (state) {
        state.loading += 1
    }
}
