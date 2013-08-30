

def make_instance_index_subsets(num_instances, num_subsets):

    test_instance_index_subsets = [[] for i in range(num_subsets)]

    for subset_index in range(num_subsets):

        instance_index = subset_index

        while instance_index < num_instances:

            test_instance_index_subsets[subset_index].append(instance_index)

            instance_index += num_subsets
        
    print test_instance_index_subsets

    return test_instance_index_subsets

num_instances = 12
num_subsets = 1

test_instance_index_subsets = make_instance_index_subsets(num_instances, num_subsets)


