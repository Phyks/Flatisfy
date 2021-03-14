<template>
    <div>
        <template v-for="n in range(5)">
            <button v-bind:key="n" v-on:mouseover="handleHover(n)" v-on:mouseout="handleOut()" v-on:click="updateNotation(n)">
                <i class="fa" v-bind:class="{'fa-star': n < notation, 'fa-star-o': n >= notation}" aria-hidden="true"></i>
            </button>
        </template>
    </div>
</template>

<script>

import { range } from '../tools'
import 'flatpickr/dist/flatpickr.css'

export default {
    data () {
        return {
            'overloadNotation': null
        }
    },

    props: ['flat'],

    computed: {
        notation () {
            if (this.overloadNotation) {
                return this.overloadNotation
            }
            return this.flat.notation
        }
    },

    methods: {
        updateNotation (notation) {
            notation = notation + 1

            if (notation === this.flat.notation) {
                this.flat.notation = 0
                this.$store.dispatch('updateFlatNotation', { flatId: this.flat.id, newNotation: 0 })
                this.$store.dispatch('updateFlatStatus', { flatId: this.flat.id, newStatus: 'new' })
            } else {
                this.flat.notation = notation
                this.$store.dispatch('updateFlatNotation', { flatId: this.flat.id, newNotation: notation })
                this.$store.dispatch('updateFlatStatus', { flatId: this.flat.id, newStatus: 'followed' })
            }
        },

        handleHover (n) {
            this.overloadNotation = n + 1
        },

        handleOut () {
            this.overloadNotation = null
        },

        range: range
    }
}
</script>

<style scoped>
button {
    border: none;
    width: auto;
    background-color: transparent;
}
</style>
