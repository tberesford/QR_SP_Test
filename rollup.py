import sys
import requests
import pandas as pd
import json

URL = 'https://interviewbom.herokuapp.com/'


class Tree:
    def __init__(self, part_id):
        """
        Initialise node
        :param part_id: Id of part to have node made.
        """
        self.name = part_id
        self.child = []
        self.quantity = 0
        self.total_quantity = 0
        self.parent = None
        self.id = None

    def add_child(self, part_id):
        """
        Adds child connection
        :param part_id:
        :return: None
        """
        self.child.insert(0, part_id)

    def add_parent(self, parent_id):
        """
        Set parent
        :param parent_id:
        :return: None
        """
        self.parent = parent_id

    def add_quantity(self, quantity):
        """
        Set quantity
        :param quantity:
        :return: None
        """
        self.quantity = quantity

    def add_total_quantity(self):
        """
        Creates the total quantity
        :return: None
        """
        self.total_quantity = self.parent.total_quantity * self.quantity


def iterate_children(child):
    """
    Recursive function iterating through each node, calculating
    its total quantity.
    :param child: The current node at a given time.
    :return: None.
    """
    while len(child.child) > 0:
        current_child = child.child.pop(0)
        if current_child.total_quantity == 0:  # Zero to prevent rewrite as node connects to one node at a given time.
            current_child.add_total_quantity()
        iterate_children(current_child)


def get_part_number(part_id):
    """
    Obtains the part number of parts.
    :param part_id: part_id to pass into url.
    :return: The part number assigned to part_id.
    """
    res = requests.get(f'{URL}part/{part_id}/')
    if res.status_code == 200:
        data = json.loads(res.content)
        return data['part_number']
    else:
        print('Error fetching part name.')
        return None


def main(data):
    """
    Takes the data from the REST api and processes it
    to form a tree data structure. Then calculates the
    total quantities of each branch.
    :param data: Data loaded from the REST api
    :return: Dataframe of the resulting data
    """
    js = json.loads(data)
    data = js["data"]
    df = pd.DataFrame(data)
    root_id = df.iloc[0]['part_id']
    nodes = [Tree(part[1]['part_id']) for part in df.iterrows()]  # Create a node/object of Tree for each part_id

    for node in nodes:  # Add the respective qualities and create connections of child to parent for each node
        if node.name != root_id:
            parent = float(df.loc[df['part_id'] == node.name]['parent_part_id'])
            id = int(df.loc[df['part_id'] == parent]['id'])
            quantity = int(df.loc[df['part_id'] == node.name]['quantity'])

            node.add_quantity(quantity)
            nodes[id].add_child(node)
            node.add_parent(nodes[id])

            if node.parent.name == root_id:  # Root node total quantity is its specified quantity (1)
                node.total_quantity = quantity
        else:
            node.quantity = 1
            node.total_quantity = 1

    root = nodes[0]
    [iterate_children(children) for children in root.child]  # Call function for each child of root

    part_numbers = {}
    for node in nodes:
        part_number = get_part_number(int(node.name))
        if part_number not in part_numbers.keys():
            part_numbers[part_number] = node.total_quantity
        else:
            part_numbers[part_number] += node.total_quantity

    part_df = pd.DataFrame(columns=['Part Number', 'Total Quantity'])
    part_df['Part Number'] = part_numbers.keys()
    part_df['Total Quantity'] = part_numbers.values()

    return part_df


if __name__ == "__main__":
    try:
        outfile = sys.argv[1]
        if 'xlsx' != outfile.split('.')[-1]:
            outfile += '.xlsx'
        res = requests.get(f'{URL}bom/')
        if res.status_code == 200:
            print('Beginning process...')
            data = res.content
            output = main(data)
            output.to_excel(outfile, index=False)
            print(f'Data saved at {outfile}.')
        else:
            print(f'Connection failed: {res.status_code}')
    except Exception as e:
        print(e)
