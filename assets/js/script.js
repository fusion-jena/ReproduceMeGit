// App initialization code goes here
var d3 = require('d3');
$(document).ready(function() {
    // $(function() {
    var repository_id = (window.location.pathname).split("/").pop(-1);
    var notebook_id, cell_types;
    const CODE_CELL_TYPE = 0,
          OTHER_CELL_TYPE = 1,
          ALL_CELL_TYPE = 2;

    $("#registerForm").on('submit', function(event) {
        $('#loadingDiv').show();
    });

    function get_config(data_obj) {
        if (!data_obj) {
            data = {
                datasets: [{
                    labels: 'No data',
                    backgroundColor: colors,
                    data: []
                }]
            }
            text = ''
        } else {
            data = {
                datasets: [{
                    data: data_obj['data'],
                    backgroundColor: colors,
                }],
                labels: data_obj['labels'],
            }
            text = data_obj['title']
        }
        config = {
            type: 'pie',
            data: data,
            options: {
                title: {
                    display: true,
                    position: 'bottom',
                    text: text,
                    fontStyle: 'bold',
                    fontSize: 14,
                    fontColor: 'black',
                },
                legend: {
                    labels: {
                        fontStyle: 'bold',
                        fontColor: 'black'
                    }
                },
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    datalabels: {
                        color: '#fff',
                        labels: {
                            title: {
                                font: {
                                    weight: 'bold',
                                    size: 16,
                                }
                            },
                        },
                    },
                },
            }
        }
        return config;
    }

    function generatereproducednbchart() {
        colors = ["#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#c45850",
            "#E57373", "#F06292", "#CE93D8", "#B39DDB", "#9FA8DA",
            "#90CAF9", "#4DB6AC", "#DCE775", "#1B5E20"
        ]

        $.ajax({
            url: '/reproducednb/' + repository_id,
            success: function(response) {
                if (!response) {
                    $('#rmoverview').html("No Notebooks data available");
                } else {
                    full_data = JSON.parse(response);
                    var exception_error = full_data['exception_error']
                    var nb_finished_unfinished_executions = full_data['nb_finished_unfinished_executions']
                    var nb_results_difference = full_data['nb_results_difference']
                    var validity_notebooks = full_data['validity_notebooks']
                    var nb_execution_count = full_data['nb_execution_count']
                    var nb_output_cell_count = full_data['nb_output_cell_count']

                    context = document.getElementById('validitynotebooksnb-chart');
                    config = get_config(validity_notebooks)
                    new Chart(context, config);

                    context = document.getElementById('exceptionerrornb-chart');
                    config = get_config(exception_error)
                    new Chart(context, config);

                    context = document.getElementById('nbfinishedunfinishedexecutions-chart');
                    config = get_config(nb_finished_unfinished_executions)
                    new Chart(context, config);

                    context = document.getElementById('nbresultsdifference-chart');
                    config = get_config(nb_results_difference)
                    new Chart(context, config);

                    context = document.getElementById('nbexecutioncount-chart');
                    config = get_config(nb_execution_count)
                    new Chart(context, config);

                    context = document.getElementById('nboutputcellcount-chart');
                    config = get_config(nb_output_cell_count)
                    new Chart(context, config);
                }
            }
        });

    }

    if (!isNaN(repository_id)) {
        generatereproducednbchart();
    }

    // D3 svg for the graph for execution order of notebooks
    // Adapted from (http://bl.ocks.org/fancellu/2c782394602a93921faff74e594d1bb1)
    var svg = d3.select("svg")
        .classed("svg-content", true),
        width = +svg.attr("width"),
        height = +svg.attr("height"),
        node,
        link;


    var simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(function(d) {
            return d.id;
        }).distance(100).strength(1))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2));

    function updateGraph(links, nodes) {
        svg.selectAll("*").remove()


        svg.append('defs').append('marker')
            .attrs({
                'id': 'arrowhead',
                'viewBox': '-0 -5 10 10',
                'refX': 13,
                'refY': 0,
                'orient': 'auto',
                'markerWidth': 13,
                'markerHeight': 13,
                'xoverflow': 'visible'
            })
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999')
            .style('stroke', 'none');



        link = svg.selectAll(".link")
            .data(links)
            .enter()
            .append("line")
            .attr("class", "link")
            .attr('marker-end', 'url(#arrowhead)')

        link.append("title")
            .text(function(d) {
                return d.type;
            });

        edgepaths = svg.selectAll(".edgepath")
            .data(links)
            .enter()
            .append('path')
            .attrs({
                'class': 'edgepath',
                'fill-opacity': 0,
                'stroke-opacity': 0,
                'id': function(d, i) {
                    return 'edgepath' + i
                }
            })
            .style("pointer-events", "none");

        edgelabels = svg.selectAll(".edgelabel")
            .data(links)
            .enter()
            .append('text')
            .style("pointer-events", "none")
            .attrs({
                'class': 'edgelabel',
                'id': function(d, i) {
                    return 'edgelabel' + i
                },
                'font-size': 10,
                'fill': '#aaa'
            });

        edgelabels.append('textPath')
            .attr('xlink:href', function(d, i) {
                return '#edgepath' + i
            })
            .style("text-anchor", "middle")
            .style("pointer-events", "none")
            .attr("startOffset", "50%")
            .text(function(d) {
                return d.type
            });

        node = svg.selectAll(".node")
            .data(nodes)
            .enter()
            .append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended)
            );

        node.append("circle")
            .attr("r", 10)
            .style("fill", "#0069D9")
        // .style("fill", function (d, i) {return colors(i);})

        node.append("title")
            .text(function(d) {
                return d.id;
            });

        node.append("text")
            .attr("dy", -3)
            .text(function(d) {
                return d.label;
            });
        // .text(function (d) {return d.name+":"+d.label;});

        simulation
            .nodes(nodes)
            .on("tick", ticked);

        simulation.force("link")
            .links(links);
    }

    function ticked() {
        link
            .attr("x1", function(d) {
                return d.source.x;
            })
            .attr("y1", function(d) {
                return d.source.y;
            })
            .attr("x2", function(d) {
                return d.target.x;
            })
            .attr("y2", function(d) {
                return d.target.y;
            });

        node
            .attr("transform", function(d) {
                return "translate(" + d.x + ", " + d.y + ")";
            });

        edgepaths.attr('d', function(d) {
            return 'M ' + d.source.x + ' ' + d.source.y + ' L ' + d.target.x + ' ' + d.target.y;
        });

        edgelabels.attr('transform', function(d) {
            if (d.target.x < d.source.x) {
                var bbox = this.getBBox();

                rx = bbox.x + bbox.width / 2;
                ry = bbox.y + bbox.height / 2;
                return 'rotate(180 ' + rx + ' ' + ry + ')';
            } else {
                return 'rotate(0)';
            }
        });
    }


    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
        d.fx = undefined;
        d.fy = undefined;
    }

    function getGraphCellType() {
        // check which checkboxes are checked and update the graph based on the cell type
        var el = document.getElementById('notebookcelltype');
        var celltype = el.getElementsByTagName('input');
        var len = celltype.length;
        checkbox_values = []
        cell_types = ALL_CELL_TYPE
        for (var i = 0; i < len; i++) {
            if (celltype[i].type === 'checkbox' && celltype[i].checked === true) {
                checkbox_values.push(celltype[i].value)
            }
        }
        if (checkbox_values.length === 2) {
            cell_types = ALL_CELL_TYPE
        } else if (checkbox_values.length == 1 && checkbox_values[0] === 'codecells') {
            cell_types = CODE_CELL_TYPE
        } else if (checkbox_values.length == 1 && checkbox_values[0] === 'othercells') {
            cell_types = OTHER_CELL_TYPE
        }

        $.ajax({

            // API call for get notebook's execution order in JSON
            url: '/get_network_json/' + repository_id + '/' + notebook_id + '/' + cell_types,
            success: function(response) {
                if (!response) {
                    console.log("Failure");
                } else {
                    // Set the graph
                    var graph = response
                    //Update graph with the response
                    updateGraph(graph.links, graph.nodes)
                }

            }
        });
    }


    function setEventHandlerCheckbox() {
        // get cell type checkboxes container
        var el = document.getElementById('notebookcelltype');

        // get cell type input element refrence in checkboxes container
        var celltype = el.getElementsByTagName('input');

        // get length
        var len = celltype.length;

        // call getgraph() function to onclick event on every checkbox
        for (var i = 0; i < len; i++) {
            if (celltype[i].type === 'checkbox') {
                celltype[i].onclick = getGraphCellType;
            }
        }
    }



    function getExecutionOrderJson() {
        $.ajax({

            // API call for get notebook's execution order in JSON
            url: '/get_network_json/' + repository_id + '/' + notebook_id + '/' + cell_types,
            success: function(response) {
                if (!response) {
                    console.log("Failure");
                } else {

                    // Set the hidden cell type checkbox option to visible
                    setVisibleCellTypeOption()

                    // add eventhandler for onclick event for every click on the cell type checkbox
                    setEventHandlerCheckbox()

                    // Set the graph
                    var graph = response
                    //Update graph with the response
                    updateGraph(graph.links, graph.nodes)
                }
            }
        });
    }

    function setVisibleCellTypeOption() {
        // Set the hidden cell type checkbox option to visible
        var elem = document.getElementById("celltypeform");
        elem.style.visibility = 'visible';
    }

    $(".dropdown-menu a").click(function() {
        // Add active class to the selected option and remove active class from previously selected options
        $(this).addClass('active').siblings().removeClass('active');

        // Get the notebook id of the selected notebook
        notebook_id = $(this).attr('value');

        // Initial load all cell type graph
        cell_types = ALL_CELL_TYPE;

        getExecutionOrderJson();

    });


})