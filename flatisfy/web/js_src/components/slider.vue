<template>
<div @keydown="closeModal">
    <isotope ref="cpt" :options="isotopeOptions" v-images-loaded:on.progress="layout" :list="photos">
        <div v-for="(photo, index) in photosURLOrLocal" :key="photo">
            <img :src="photo" v-on:click="openModal(index)"/>
        </div>
    </isotope>

    <div class="modal" ref="modal" :aria-label="$t('slider.Fullscreen_photo')" role="dialog">
        <span class="close"><button v-on:click="closeModal" :title="$t('common.Close')" :aria-label="$t('common.Close')">&times;</button></span>

        <img class="modal-content" :src="photosURLOrLocal[modalImgIndex]">
    </div>
</div>
</template>

<script>
import isotope from 'vueisotope'
import imagesLoaded from 'vue-images-loaded'

export default {
    props: [
        'photos'
    ],

    components: {
        isotope
    },

    computed: {
        photosURLOrLocal() {
            return this.photos.map(photo => {
                if (photo.local) {
                    return `/data/img/${photo.local}`;
                }
                return photo.url;
            });
        },
    },

    created () {
        window.addEventListener('keydown', event => {
            if (!this.isModalOpen) {
                return
            }

            if (event.key === 'Escape') {
                this.closeModal()
            } else if (event.key === 'ArrowLeft') {
                this.modalImgIndex = Math.max(
                    this.modalImgIndex - 1,
                    0
                )
            } else if (event.key === 'ArrowRight') {
                this.modalImgIndex = Math.min(
                    this.modalImgIndex + 1,
                    this.photos.length - 1
                )
            }
        })
    },

    directives: {
        imagesLoaded
    },

    data () {
        return {
            'isotopeOptions': {
                layoutMode: 'masonry',
                masonry: {
                    columnWidth: 275
                }
            },
            'isModalOpen': false,
            'modalImgIndex': 0
        }
    },

    methods: {
        layout () {
            this.$refs.cpt.layout('masonry')
        },

        openModal (index) {
            this.isModalOpen = true
            this.modalImgIndex = index

            this.$refs.modal.style.display = 'block'
        },

        closeModal () {
            this.isModalOpen = false
            this.$refs.modal.style.display = 'none'
        }
    }
}
</script>

<style scoped>
.item img {
    max-width: 250px;
    margin: 10px;
    cursor: pointer;
}

.item img:hover {
    opacity: 0.7;
}

.modal {
    display: none;
    position: fixed;
    z-index: 10000;
    padding-top: 100px;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgb(0,0,0);
    background-color: rgba(0,0,0,0.9);
}

.modal-content {
    margin: auto;
    display: block;
    max-height: 80%;
    max-width: 100%;
}

.close {
    position: absolute;
    top: 15px;
    right: 35px;
    color: #f1f1f1;
    font-size: 40px;
    font-weight: bold;
    transition: 0.3s;
}

.close button {
    font-size: 1em;
    border: none;
    background: transparent;
    cursor: pointer;
}

.close:hover,
.close:focus {
    color: #bbb;
    text-decoration: none;
    cursor: pointer;
}
</style>
