// App initialization code goes here

$(document).ready(function () {
    // $(function() {
        var repository_id = (window.location.pathname).split("/").pop(-1);

        $("#registerForm").on('submit', function(event){
            $('#loadingDiv').show();
        });

        function get_config(data_obj) {
            if (!data_obj) {
                data = {
                    datasets: [{
                      labels:'No data',
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
            colors = ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850",
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


})