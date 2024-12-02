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
        # TODO: Implement this method
        return []
        def is_dead_end(matrix, row_idx, col_idx):
            if matrix[row_idx][col_idx] != 0:
                return False

            walls = 0
            if row_idx == 0 or matrix[row_idx - 1][col_idx] == 1:
                walls += 1
            if row_idx == len(matrix) - 1 or matrix[row_idx + 1][col_idx] == 1:
                walls += 1
            if col_idx == 0 or matrix[row_idx][col_idx - 1] == 1:
                walls += 1
            if col_idx == len(matrix[0]) - 1 or matrix[row_idx][col_idx + 1] == 1:
                walls += 1
        
            return walls >= 3
            
        dead_ends = []
        for row_idx, row in enumerate(matrix):
            for col_idx, value in enumerate(row):
                if is_dead_end(matrix, row_idx, col_idx):
                    dead_ends.append([row_idx, col_idx])
                    # Check for straight line of zeros
                    if row_idx > 0 and matrix[row_idx - 1][col_idx] == 0:
                        for i in range(row_idx, len(matrix)):
                            if matrix[i][col_idx] != 0 or not is_dead_end(matrix, i, col_idx):
                                break
                            dead_ends.append([i, col_idx])
                    if col_idx > 0 and matrix[row_idx][col_idx - 1] == 0:
                        for j in range(col_idx, len(matrix[0])):
                            if matrix[row_idx][j] != 0 or not is_dead_end(matrix, row_idx, j):
                                break
                            dead_ends.append([row_idx, j])
                
        return dead_ends
