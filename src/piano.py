def hilbert_curve(n):
    """Generates Hilbert curve points for a grid of size n x n."""
    points = []
    for d in range(n * n):
        x, y = d2xy(n, d)
        points.append((x, y))
    return points

def d2xy(n, d):
    """Convert Hilbert distance d to coordinates x and y."""
    x = y = 0
    t = d
    s = 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        x, y = rotate(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t = t // 4
        s *= 2
    return x, y

def rotate(n, x, y, rx, ry):
    """Rotate/flip a quadrant appropriately."""
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        # Swap x and y
        x, y = y, x
    return x, y

def generate_hilbert_path(width, height, sight_range):
    # Calculate the dimensions of the coarser grid
    coarse_width = (width + sight_range - 1) // sight_range
    coarse_height = (height + sight_range - 1) // sight_range
    n = 1
    while n < max(coarse_width, coarse_height):
        n *= 2

    # Generate Hilbert curve points on the coarser grid
    points = hilbert_curve(n)

    # Clip points to the coarse grid size
    path = [(x, y) for x, y in points if x < coarse_width and y < coarse_height]

    # Scale the points back to the original grid
    scaled_path = [(x * sight_range, y * sight_range) for x, y in path if x * sight_range < width and y * sight_range < height]

    return scaled_path

def main():
    # Read inputs
    width = int(input("Enter the width of the grid: "))
    height = int(input("Enter the height of the grid: "))
    sight_range = int(input("Enter the sight range (between 2 and 6): "))

    # Validate sight range
    if not 2 <= sight_range <= 6:
        print("Sight range must be between 2 and 6.")
        return

    # Generate the path
    path = generate_hilbert_path(width, height, sight_range)

    # Output the points, one per line
    for point in path:
        print(point)

if __name__ == "__main__":
    main()
