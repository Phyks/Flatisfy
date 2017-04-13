<template>
    <div>
        <h2>{{ capitalize($t("status." + $route.name)) }}</h2>
        <template v-if="Object.keys(postalCodesFlatsBuckets).length">
            <template v-for="(postal_code_data, postal_code) in postalCodesFlatsBuckets">
                <h3>{{ postal_code_data.name }} ({{ postal_code }}) - {{ postal_code_data.flats.length }} {{ $tc("common.flats", 42) }}</h3>
                <FlatsTable :flats="postal_code_data.flats"></FlatsTable>
            </template>
        </template>
        <template v-else>
            <p>{{ $t("flatListing.no_available_flats") }}</p>
        </template>
    </div>
</template>

<script>
import { capitalize } from '../tools'

import FlatsTable from '../components/flatstable.vue'

export default {
    components: {
        FlatsTable
    },

    created () {
        // Fetch flats when the component is created
        this.$store.dispatch('getAllFlats')
    },

    computed: {
        postalCodesFlatsBuckets () {
            return this.$store.getters.postalCodesFlatsBuckets(flat => flat.status === this.$route.name)
        }
    },

    methods: {
        capitalize: capitalize
    }
}
</script>
