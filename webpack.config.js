module.exports = {
    entry: './flatisfy/web/js_src/main.js',
    output: {
        path: __dirname + '/flatisfy/web/static/js/',
        filename: 'bundle.js'
    },
    module: {
        loaders: [
            {
                test: /\.js$/,
                exclude: /(node_modules|bower_components)/,
                use: {
                    loader: 'babel-loader'
                }
            },
            {
                test: /\.vue$/,
                loader: 'vue-loader',
                options: {
                    loaders: {
                        js: 'babel-loader'
                    }
                }
            },
            {
                test: /\.css$/,
                loader: 'style-loader!css-loader'
            },
            {
                test: /\.(jpe?g|png|gif|svg)$/i,
                loaders: [
                    'file-loader?hash=sha512&digest=hex&name=[hash].[ext]',
                    {
                        loader: 'image-webpack-loader',
                        query: {
                            bypassOnDebug: true,
                            'optipng': {
                                optimizationLevel: 7
                            },
                            'gifsicle': {
                                interlaced: false
                            }
                        }
                    }
                ]
            }
        ]
    },
    resolve: {
        alias: {
            'masonry': 'masonry-layout',
            'isotope': 'isotope-layout'
        }
    }
}
