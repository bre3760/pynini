/*****************************************************************************
 * The MIT License (MIT)
 *
 * Copyright (c) 2015 Sam Wilson
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 *****************************************************************************/
(function() {
    var FlotWidgetPlugin = function (settings) {
        var self = this;
        var currentSettings = settings;

        var currentData = [];
        var $holder;
        var plot;
        var myContainer;

        function addSeries() {
            var series = {data: [],
                            points: {show: currentSettings.points},
                            lines: {show: true}};
            currentData.push(series);
            return series;
        }

        function dispose(erase) {
            myContainer = undefined;

            if (erase) {
                currentData = [];
            }

            if (plot) {
                plot.shutdown();
                plot = undefined;
            }

            if ($holder) {
                $holder.remove();
                $holder = undefined;
            }
        }

        self.render = function(container) {
            dispose(false);
            var $container = $(container);
            myContainer = container;
            $holder = $('<div></div>')
                .css({width: $container.width(),
                      height: currentSettings.height*60 - 10})
                .appendTo($container);
            var options = {};
            if (currentSettings.x_timestamp) {
                options.xaxis = {mode: "time"};
            }
            plot = $.plot($holder, currentData, options);
        };

        self.getHeight = function() {
            return currentSettings.height;
        };

        self.onSettingsChanged = function(newSettings) {
            currentSettings = newSettings;
            self.render(myContainer);
            plot.getOptions().series.points.show = currentSettings.points;
        };

        self.onCalculatedValueChanged = function(settingName, newValue) {
            // Check if this is the correct setting.
            if (settingName != "value") {
                return;
            }

            var redraw = false;

            // Push new data and remove extra data points.
            for (var ii = 0; ii < newValue.length; ii++) {
                var series;
                if (ii >= currentData.length) {
                    series = addSeries();
                } else {
                    series = currentData[ii];
                }

                var data = series.data;
                if (!data.length || !_.isEqual(data[data.length-1], newValue[ii])) {
                    series.data.push(newValue[ii]);
                    series.data = _.sortBy(series.data, 0);
                    series.data = _.last(series.data, currentSettings.max_points);
                    redraw = true;
                }
            }

            if (redraw) {
                plot.setData(currentData);
                plot.setupGrid();
                plot.draw();
            }
        };

        self.onDispose = function() {
            dispose(true);
        };
    };

    freeboard.loadWidgetPlugin({
        type_name:          "flot_line_plugin",
        display_name:       "Flot Line",
        description:        "Line graph provided by flot",
        external_scripts:   [
                                "//cdnjs.cloudflare.com/ajax/libs/flot/0.8.3/jquery.flot.min.js",
                                "https://cdnjs.cloudflare.com/ajax/libs/flot/0.8.3/jquery.flot.time.js"
                            ],
        settings:           [
                                {
                                    name:           "height",
                                    display_name:   "Height",
                                    type:           "number",
                                    description:    "in blocks",
                                    default_value:  2
                                },
                                {
                                    name:           "value",
                                    display_name:   "Value",
                                    type:           "calculated",
                                },
                                {
                                    name:           "max_points",
                                    display_name:   "Max Points",
                                    type:           "number",
                                    default_value:  20,
                                },
                                {
                                    name:           "x_timestamp",
                                    display_name:   "X Axis Timestamp",
                                    type:           "boolean"
                                },
                                {
                                    name:           "points",
                                    display_name:   "Show Points",
                                    type:           "boolean"
                                }
                            ],

        newInstance:        function(settings, newInstanceCB) {
                                newInstanceCB(new FlotWidgetPlugin(settings));
                            }
    });
}());
