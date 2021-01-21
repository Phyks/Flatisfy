<template>
    <div class="flex-row">
        <div class="flex" style="overflow: auto;">
            <FlatsMap :flats="flatsMarkers" :places="timeToPlaces" v-on:select-flat="selectFlat($event)"></FlatsMap>
            <h2>
            {{ $t("home.new_available_flats") }}
            <template v-if="lastUpdate">
                <label class="show-last-update">
                {{ $t("home.Last_update") }} {{ lastUpdate.fromNow() }}
                </label>
            </template>
            <label class="show-expired-flats-label">
                <input type="checkbox" class="show-expired-flats-checkbox" v-model="showExpiredFlats" />
                {{ $t("home.show_expired_flats") }}
            </label>
            </h2>

            <template v-if="Object.keys(postalCodesFlatsBuckets).length > 0">
                <template v-for="(postal_code_data, postal_code) in postalCodesFlatsBuckets">
                    <h3>
                        {{ postal_code_data.name || $t('common.Unknown') }}
                        <span v-if="postal_code !== 'undefined'">
                            ({{ postal_code }})
                        </span>
                        - {{ postal_code_data.flats.length }} {{ $tc("common.flats", postal_code_data.flats.length) }}
                    </h3>
                    <FlatsTable :flats="postal_code_data.flats" :key="postal_code"></FlatsTable>
                </template>
            </template>
            <template v-else-if="isLoading">
                <p>{{ $t("common.loading") }}</p>
            </template>
            <template v-else>
                <p>{{ $t("flatListing.no_available_flats") }}</p>
            </template>
        </div>
        <div v-if="selectedFlat" class="flex">
            <Flat :flat="selectedFlat"></Flat>
        </div>
    </div>
</template>

<script>
import FlatsMap from '../components/flatsmap.vue'
import FlatsTable from '../components/flatstable.vue'
import Flat from '../components/flat.vue'
import moment from 'moment'

export default {
    components: {
        FlatsMap,
        FlatsTable,
        Flat
    },

    created () {
        document.title = 'Flatisfy'  // Set title

        // Fetch flats when the component is created
        this.$store.dispatch('getAllFlats')
        // Fetch time to places when the component is created
        this.$store.dispatch('getAllTimeToPlaces')
        // Fetch application metadata when the component is created
        this.$store.dispatch('getMetadata')
    },

    data () {
        return {
            showExpiredFlats: false,
            selectedFlat: undefined
        }
    },

    methods: {
        selectFlat: async function (flatId) {
            if (flatId) {
                await this.$store.dispatch('getFlat', { flatId })
                this.selectedFlat = await this.$store.getters.flat(flatId)
            } else {
                this.selectedFlat = undefined
            }
        }
    },

    computed: {
        postalCodesFlatsBuckets () {
            return this.$store.getters.postalCodesFlatsBuckets(flat =>
                flat.status === 'new' &&
                (this.showExpiredFlats || !flat.is_expired)
            )
        },
        flatsMarkers () {
            return this.$store.getters.flatsMarkers(this.$router, flat =>
                flat.status === 'new' &&
                (this.showExpiredFlats || !flat.is_expired)
            )
        },
        timeToPlaces () {
            return this.$store.getters.allTimeToPlaces
        },
        lastUpdate () {
            var metadata = this.$store.getters.metadata
            var lastUpdateDate = moment.unix(metadata['last_update'])
            if (!lastUpdateDate.isValid()) {
                lastUpdateDate = 0
            }
            return lastUpdateDate
        },
        isLoading () {
            return this.$store.getters.isLoading
        }
    }
}
</script>

<style scoped>
h2 {
    display: flex;
    justify-content: space-between;
}
.flex-row {
    display:flex;
}
.flex {
    flex: 1;
}
table {
    margin-left: 0;
    margin-right: 0;
    width: 100%;
}

.show-expired-flats-label {
    font-weight: initial;
    font-size: initial;
}

.show-last-update {
    font-weight: initial;
    font-size: initial;
}
</style>
