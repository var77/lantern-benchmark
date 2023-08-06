from scripts.script_utils import execute_sql, convert_number_to_string, VALID_METRICS, METRICS_WITH_K, VALID_EXTENSIONS, VALID_EXTENSIONS_AND_NONE, VALID_DATASETS, VALID_QUERY_DATASETS, SUGGESTED_K_VALUES
import recall_experiment
import select_experiment
import disk_usage_experiment
import create_experiment

# Parameter sets

def get_found_parameter_sets(metric_type):
    if metric_type in METRICS_WITH_K:
        sql = 'SELECT database, dataset, n, k FROM experiment_results WHERE metric_type = %s'
    else:
        sql = 'SELECT database, dataset, n FROM experiment_results WHERE metric_type = %s'
  
    found_parameter_sets = execute_sql(sql, data=(metric_type,), select=True)
    found_parameter_sets = {(database, dataset, convert_number_to_string(n), *rest) for (database, dataset, n, *rest) in found_parameter_sets}
    return found_parameter_sets

def get_extension_parameter_sets(extension, metric_type):
    valid_parameter_sets = []
    for dataset in VALID_DATASETS.keys():
        valid_N = VALID_QUERY_DATASETS[dataset] if metric_type == 'recall' else VALID_DATASETS[dataset]
        for N in valid_N:
            if metric_type in METRICS_WITH_K:
                for K in SUGGESTED_K_VALUES:
                    valid_parameter_sets.append((extension, dataset, N, K))
            else:
                valid_parameter_sets.append((extension, dataset, N))
    return valid_parameter_sets

def get_missing_parameter_sets(metric_type):
    found_parameter_sets = get_found_parameter_sets(metric_type)

    valid_parameter_sets = []
    for extension in VALID_EXTENSIONS:
        if metric_type == 'disk usage (bytes)' and extension == 'none':
            continue
        valid_parameter_sets.extend(get_extension_parameter_sets(extension, metric_type))

    missing_parameter_sets = [parameter_set for parameter_set in valid_parameter_sets if parameter_set not in found_parameter_sets]
    return missing_parameter_sets

def group_parameter_sets_with_k(parameter_sets):
    grouped_dict = {}
    for parameter_set in parameter_sets:
        extension, dataset, N, K = parameter_set
        key = (extension, dataset, N)
        if key in grouped_dict:
            grouped_dict[key].append(K)
        else:
            grouped_dict[key] = [K]
    return [(*key, values) for key, values in grouped_dict.items()]

# Generate results

def validate(metric_type, extension=None):
    assert metric_type in VALID_METRICS
    if extension is not None:
        if 'select' in metric_type or 'recall' in metric_type:
            assert extension in VALID_EXTENSIONS_AND_NONE
        else:
            assert extension in VALID_EXTENSIONS

def get_generate_result(metric_type):
    if metric_type == 'select (tps)':
        return select_experiment.generate_result
    if metric_type == 'select (latency ms)':
        return select_experiment.generate_result
    if metric_type == 'recall':
        return recall_experiment.generate_result
    if metric_type == 'disk usage (bytes)':
        return disk_usage_experiment.generate_result
    if metric_type == 'create (latency ms)':
        return create_experiment.generate_result

def generate_extension_results(extension, metric_type):
    validate(metric_type, extension)

    parameter_sets = get_extension_parameter_sets(extension, metric_type)
    if metric_type in METRICS_WITH_K:
        parameter_sets = group_parameter_sets_with_k(parameter_sets)
    for parameter_set in parameter_sets:
      print(parameter_set)
    print()
    generate_result = get_generate_result(metric_type)
    for parameter_set in parameter_sets:
        generate_result(*parameter_set)

def generate_missing_results(metric_type):
    validate(metric_type)

    parameter_sets = get_missing_parameter_sets(metric_type)
    if metric_type in METRICS_WITH_K:
        parameter_sets = group_parameter_sets_with_k(parameter_sets)
    if len(parameter_sets) > 0:
        print('Missing parameter sets')
        for parameter_set in parameter_sets:
            print(parameter_set)
        print()
        generate_result = get_generate_result(metric_type)
        for parameter_set in parameter_sets:
            generate_result(*parameter_set)
    else:
        print('No missing parameter sets')