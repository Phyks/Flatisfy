<template>
    <div>
        <template v-if="isLoading">
            <p>{{ $t("common.loading") }}</p>
        </template>
        <Flat :flat="flat"></Flat>
    </div>
</template>

<script>

import Flat from '../components/flat.vue'

export default {
    components: {
        Flat
    },
    created () {
        document.title = this.title  // Set title

        // Fetch data when the component is created
        this.fetchData()

        // Scrolls to top when view is displayed
        window.scrollTo(0, 0)
    },

    watch: {
        // Fetch data again when the component is updated
        '$route': 'fetchData',
        title () {
            document.title = this.title
        }
    },

    computed: {
        isLoading () {
            return this.$store.getters.isLoading
        },
        title () {
            return 'Flatisfy - ' + this.$route.params.id
        },
        flat () {
            return this.$store.getters.flat(this.$route.params.id)
        }
    },

    methods: {
        fetchData () {
            this.$store.dispatch('getFlat', { flatId: this.$route.params.id })
        }
    }
}
</script>

