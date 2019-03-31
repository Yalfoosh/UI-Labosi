import copy


class TraceableTree:
    def __init__(self, state, direction=None, cost=1, parent=None):
        self.state = state
        self.direction = direction
        self.cost = cost
        self.parent = parent

    def get_path(self):
        mock_node = self
        path = list()

        while mock_node.parent is not None:
            path.append(mock_node.direction)
            mock_node = mock_node.parent

        path.reverse()
        return path
