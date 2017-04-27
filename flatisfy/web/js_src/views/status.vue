<template>
    <div>
        <h2 class="btn-group">
            <button type="button" class="dropdownToggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" v-on:click="toggleDropdown()" ref="dropdownToggle">
                <span class="dashedUnderline">{{ capitalize($t("status." + $route.params.status)) }}</span>
                <i class="fa fa-caret-down"/>
            </button>
            <ul class="dropdownMenu" :class="isDropdownVisible ? '' : 'hidden'">
                <li v-for="status in available_status" :key="status" :class="$route.params.status == status.toLowerCase() ? 'active' : ''">
                    <router-link :to="{ name: 'status', params: {status: status.toLowerCase()}}" role="button">
                        {{ capitalize($t("status." + status)) }}
                    </router-link>
                </li>
            </ul>
        </h2>
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
    data () {
        return {
            'isDropdownVisible': false,
            'available_status': [
                'new',
                'followed',
                'ignored',
                'duplicate',
                'user_deleted'
            ]
        }
    },

    components: {
        FlatsTable
    },

    created () {
        // Fetch flats when the component is created
        this.$store.dispatch('getAllFlats')
    },

    mounted () {
        window.addEventListener('click', event => {
            if (event.target !== this.$refs.dropdownToggle) {
                this.isDropdownVisible = false
            }
        })
    },

    computed: {
        postalCodesFlatsBuckets () {
            return this.$store.getters.postalCodesFlatsBuckets(flat => flat.status === this.$route.params.status)
        }
    },

    methods: {
        toggleDropdown () {
            this.isDropdownVisible = !this.isDropdownVisible
        },
        capitalize: capitalize
    }
}
</script>

<style scoped>
.btn-group {
    position: relative;
    display: inline-flex;
    vertical-align: middle;
}

.btn-group > .btn {
    position: relative;
    flex: 0 1 auto;
    margin-bottom: 0;
}

.btn-group > .btn:hover {
    z-index: 2;
}

.btn-group > .btn:focus,
.btn-group > .btn:active,
.btn-group > .btn.active {
    z-index: 2;
}

.dropdownToggle {
    border: none;
    padding: 0;
    line-height: 1em;
    background-color: transparent;
    font-size: 21px;
    font-weight: 700;
    color: #333;
    font-family: "Helvetica", "Arial", sans-serif;
}

.hidden {
    display: none;
}

.dropdownMenu {
    position: absolute;
    top: 10px;
    min-width: 160px;
    background-color: white;
    z-index: 1;
    padding-left: 0;
    border-radius: .25rem;
    box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
}

.dropdownMenu li {
    list-style-type: none;
    padding-left: 1em;
    border-radius: .25rem;
}

.dropdownMenu a {
    text-decoration: none;
    color: #555;
    font-size: 0.75em;
    font-weight: normal;
}

.dashedUnderline {
    border-bottom: 1px dotted black;
}

.active {
    background-color: #0275d8;
}

.dropdownMenu li.active a {
    color: white;
}

.fa-caret-down {
    display: inline-block;
    font-size: 15px;
    margin-top: 1em;
    margin-left: 0.1em;
}

.dashedUnderline,
.fa-caret-down {
    /* Fix for alignment of caret and border-bottom */
    display: inline-block;
    float: left;
}
</style>
