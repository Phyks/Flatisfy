<template>
    <div>
        <template v-if="postalCodesFlatsBuckets && flatsMarkers">
            <FlatsMap :flats="flatsMarkers" :places="timeToPlaces"></FlatsMap>

            <h2>{{ $t("home.new_available_flats") }}</h2>
            <template v-if="Object.keys(postalCodesFlatsBuckets).length > 0">
                <template v-for="(postal_code_data, postal_code) in postalCodesFlatsBuckets">
                    <h3>{{ postal_code_data.name }} ({{ postal_code }}) - {{ postal_code_data.flats.length }} {{ $tc("common.flats", postal_code_data.flats.length) }}</h3>
                    <FlatsTable :flats="postal_code_data.flats"></FlatsTable>
                </template>
            </template>
            <template v-else>
                <p>{{ $t("flatListing.no_available_flats") }}</p>
            </template>
        </template>
        <template v-else>
            <p>{{ $t("common.loading") }}</p>
        </template>
    </div>
</template>

<script>
import FlatsMap from '../components/flatsmap.vue'
import FlatsTable from '../components/flatstable.vue'

export default {
    components: {
        FlatsMap,
        FlatsTable
    },

    created () {
        document.title = 'Flatisfy'  // Set title

        // Fetch flats when the component is created
        this.$store.dispatch('getAllFlats')
        // Fetch time to places when the component is created
        this.$store.dispatch('getAllTimeToPlaces')
    },

    computed: {
        postalCodesFlatsBuckets () {
            return this.$store.getters.postalCodesFlatsBuckets(flat => flat.status === 'new')
        },
        flatsMarkers () {
            return this.$store.getters.flatsMarkers(this.$router, flat => flat.status === 'new')
        },
        timeToPlaces () {
            return this.$store.getters.allTimeToPlaces
        }
    }
}
</script>
