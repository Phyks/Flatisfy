import * as api from '../api'
import * as types from './mutations-types'

export default {
    getAllFlats ({ commit }) {
        api.getFlats(flats => {
            commit(types.REPLACE_FLATS, { flats })
        })
    },
    getFlat ({ commit }, { flatId }) {
        api.getFlat(flatId, flat => {
            const flats = [flat]
            commit(types.MERGE_FLATS, { flats })
        })
    },
    getAllTimeToPlaces ({ commit }) {
        api.getTimeToPlaces(timeToPlaces => {
            commit(types.RECEIVE_TIME_TO_PLACES, { timeToPlaces })
        })
    },
    updateFlatStatus ({ commit }, { flatId, newStatus }) {
        api.updateFlatStatus(flatId, newStatus, response => {
            commit(types.UPDATE_FLAT_STATUS, { flatId, newStatus })
        })
    }
}
