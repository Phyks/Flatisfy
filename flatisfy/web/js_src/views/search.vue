<template>
    <div>
        <h2>Search</h2>
        <form v-on:submit="onSearch">
            <p class="search">
                <input ref="searchInput" type="text" name="query" :placeholder="$t('search.input_placeholder')"/>
                <input type="submit" :value="$t('search.Search')" />
            </p>
        </form>

        <h2>Results</h2>
        <template v-if="loading">
            {{ $t("common.loading") }}
        </template>
        <template v-else-if="Object.keys(postalCodesFlatsBuckets).length > 0">
            <template v-for="(postal_code_data, postal_code) in postalCodesFlatsBuckets">
                <h3>{{ postal_code_data.name }} ({{ postal_code }}) - {{ postal_code_data.flats.length }} {{ $tc("common.flats", Object.keys(postalCodesFlatsBuckets).length) }}</h3>
                <FlatsTable :flats="postal_code_data.flats"></FlatsTable>
            </template>
        </template>
        <template v-else>
            <p>{{ $t("flatListing.no_matching_flats") }}</p>
        </template>
    </div>
</template>

<script>
import FlatsTable from '../components/flatstable.vue'

export default {
    components: {
        FlatsTable
    },

    created () {
        this.doSearch()
    },

    watch: {
        '$route': 'doSearch'
    },

    computed: {
        postalCodesFlatsBuckets () {
            if (!this.$route.query.query || this.loading) {
                return {}
            }

            return this.$store.getters.postalCodesFlatsBuckets(
                flat => flat.status != "duplicate" && flat.status != "ignored"
            )
        },
        loading () {
            return this.$store.getters.isLoading;
        }
    },

    methods: {
        onSearch(event) {
            event.preventDefault()

            let query = this.$refs.searchInput.value
            this.$router.replace({ name: 'search', query: { query: query }})
        },

        doSearch() {
            let query = this.$route.query.query

            if (query) {
                this.$store.dispatch('doSearch', { query: query })
            }
        }
    }
}
</script>

<style scoped>
.search {
    width: 50%;
    margin: auto;
}

.search input[type="text"] {
    width: calc(85% - 10em);
}

.search input[type="submit"] {
    width: 10em;
}
</style>
