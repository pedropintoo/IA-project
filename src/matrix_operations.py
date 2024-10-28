class MatrixOperations:
    @staticmethod
    def find_ones(matrix):
        ones_coordinates = []
        for row_idx, row in enumerate(matrix):
            for col_idx, value in enumerate(row):
                if value == 1:
                    ones_coordinates.append([row_idx, col_idx])
        return ones_coordinates
    
    @staticmethod
    def find_dead_ends(matrix):
        dead_ends = [] # list of points
        for row_idx, row in enumerate(matrix):
            for col_idx, value in enumerate(row):
                if value == 0:
                    if MatrixOperations.count_neighbours(matrix, row_idx, col_idx) == 3:
                        dead_ends.append([row_idx, col_idx])
                
        return dead_ends
    
    @staticmethod
    def count_neighbours(matrix, row_idx, col_idx):
        neighbours = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                if row_idx + i < 0 or row_idx + i >= len(matrix):
                    continue
                if col_idx + j < 0 or col_idx + j >= len(matrix[0]):
                    continue
                if matrix[row_idx + i][col_idx + j] == 1:
                    neighbours += 1
        return neighbours

                