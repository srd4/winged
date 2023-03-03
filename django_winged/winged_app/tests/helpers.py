def print_container_children(container, indent = 0):
    print(" "*indent + str(container), len(container.item_set.all()))
    for i in container.container_set.all():
        indent+=1
        print_container_children(i, indent)