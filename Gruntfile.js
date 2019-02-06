module.exports = function (grunt) {
    'use strict';
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        less: {
            dist: {
                options: {
                    paths: [],
                    strictMath: false,
                    sourceMap: true,
                    outputSourceFiles: true,
                    sourceMapURL: '++resource++bda.plone.orders.css.map',
                    sourceMapFilename: 'src/bda/plone/orders/browser/resources/orders.css.map',
                    modifyVars: {
                        "isPlone": "false"
                    }
                },
                files: {
                    'src/bda/plone/orders/browser/resources/orders.css': 'src/bda/plone/orders/browser/resources/orders.less',
                }
            }
        },
        sed: {
            sed0: {
                path: 'src/bda/plone/orders/browser/resources/orders.css.map',
                pattern: 'src/bda/plone/orders/browser/resources/orders.less',
                replacement: '++resource++bda.plone.orders.less',
            }
        },
        watch: {
            scripts: {
                files: ['src/bda/plone/orders/browser/resources/orders.less'],
                tasks: ['less', 'sed']
            }
        }
    });
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-sed');
    grunt.registerTask('default', ['watch']);
    grunt.registerTask('compile', ['less', 'sed']);
};
