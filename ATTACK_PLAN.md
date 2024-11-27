### Steps to Predict the Opponent's Next Move

#### 1. **Identify the Opponent's Head and Tail**

   - We can use the **sight data** to locate the body of the opponent (`SNAKE = 4` in our sight).
   - **Determine the head**:
    - The head is the part of the snake that moves into previously unoccupied spaces (PASSAGE = 0).
   - **Determine the tail**:
    - The tail moves to the position previously occupied by the second-to-last part of the body.

#### 2. **Generate Possible Moves**

   - From the head's position, generate all valid moves:
     - Up, Down, Left, Right (considering the map boundaries and whether wrapping is possible).
   - Filter out moves that lead to **immediate collision**:
     - Collision with walls (`STONE = 1`).
     - Collision with its own body (`SNAKE = 4`).

#### 3. **Evaluate the Best Move**
   Since we do not know the rules the opponent uses, consider these heuristics:
   - **Priority 1: Move towards food (more important)**:
     ```
     - If there is food (`FOOD` or `SUPER`) in the sight range, calculate the distance to each food and prioritise moves that minimise this distance.
     - Doing this we can predict what will be the next move of the opponent.
     ```
   - **Priority 2: Default behaviour**:
     - If no food is nearby, assume the opponent will move straight unless forced to turn.
   - **Priority 3: Avoid collisions (more advanced)**:
     - If a move leads to a higher collision risk (e.g., moving closer to walls or into a constrained area), deprioritise it.  
     - I do not know if it is a good way to try to evaluate the next move of our opponent because in my opinion the majority of snakes will not have this heuristic.

#### 4. **Predict Based on Observed Patterns**
   - As the game progresses, observe how the opponent reacts to various situations:
     - Does it always move towards the nearest food? 
      ```
      If true, if we have a lenght > NUMBER, we could go near the food and be on circles around the food. The goal would be the other snake to touch in our body and die. If we do not have a lenght > NUMBER, I think it would be risky to do this because we are missing out on foods so we are not gaining points and the opponent have a high probability to touch our head and we may die. It's a balance between attack and defense.
      ```
     - Does it avoid risky paths or favour open spaces (advanced) ?
      ```
      I think this would be more difficult to infer from the opponent behaviour. However, could be a good idea to try to understand what type of exploration path the opponent have. We use a curve but I think the majority of our oppponents will do a simple movement: go up and down until they find a food. If that's the case we can take advantage and try to get the foods first.
      To sum up, I think this idea will be complicated to implement.
      ```
   - Goal: Use this information to refine our prediction model dynamically during the game.

#### 5. **Handling Wrapping**
   
   - Since we do not know if the opponent can wrap (`self.traverse`), we can assume both scenarios:
     - **Traverse = True**: Include wraparound moves in possible directions.
     - **Traverse = False**: Exclude wraparound moves.
   - Adjust based on observed behaviour during the game.

Here are a few points to consider:

1. **Secure Approach (Assume always `self.traverse=True`)**:
   - **Pros**: Simple and avoids misjudgments; ensures robust predictions.
   - **Cons**: Misses opportunities to exploit the opponent's inability to wrap. Exploiting `self.traverse=False` can yield high rewards (e.g., forcing opponents into traps or beating them to food). 
   However, it’s riskier and should be balanced with the game context (e.g., proximity to walls). Because the opponent may have `self.traverse=True` and wrap into the wall to go to the other side to kill us.

2. **Dynamic Adjustment Based on Observed Behaviour**:
   - **Worth It?**: Yes, if your strategy values exploiting weaknesses.
   - **Which indicators to look on?**: Observing an opponent not wrapping around or avoid internall walls is a strong indicator of `self.traverse=False`. For instance, if the opponent does not have any food in his sight and is only doing exploration, if he avoid a internal wall this fact is a strong indicator of `self.traverse=False`. We should try to try to estimate his sight based on our sight and how close we are from the opponent.
   - **Duration to Maintain `self.traverse=True`**: Adjust dynamically:
     - Start with `self.traverse=True` by default.
     - If the opponent behaves as if `self.traverse=False` (e.g., avoids edges), assume `self.traverse=False` but revert to `self.traverse=True` if they suddenly wrap.
     - A **few steps (~5-10)** is reasonable to mantain the `self.traverse=False`, after that we should have a more secure approach and assume `self.traverse=True`. Food and poison effects can alter the opponent's traverse state.

#### 6. **Influencing the Opponent**

   - If you want to attack the opponent, position your snake to:
     - Block their likely paths to food. Like I have mentioned before if we know the opponent always move towards the nearest food we can be on circles around the food (see explanation above).
     - Force them into risky areas or collisions.

#### 7. **Number of Players**

   - Should our strategy if instead of one opponent we have two opponents? 
        ```
        I think no because we follow a very strange exploration path as mentioned below.
        ```
#### Conclusion and key ideas

- We should try to do first the `Class OpponentMapping` (see below) where we store all the data we know. 
Then we should start by evaluating the next move based on if move towards food. If our action, would make us die due to the opponent estimation next move, that action should be huge penalized. This is crucial for survival-oriented planning. At the first I think this is enough because our agent follow a very strange exploration path and if the opponent try to kill us if we have a considerable lenght, the probability of the opponent die is huge.
However, after this is implemented we should adress the other points mentioned.
---

### Class OpponentMapping

This class should have all the data that we know about the opponent and should be updated dinamically based on observed behaviour.
The goal is to track essential information while keeping the design simple and efficient for the initial single-opponent case.
Future Scalability: Ensure the class is modular so it can handle multiple opponents by instantiating one `OpponentMapping` per opponent.

---

### **Data to Store in `Class OpponentMapping`**

#### **Immutable Data**

- **`name`**: The name of the opponent (unique identifier).

#### **Dynamic Data**

1. **Position Tracking**
   - **`head_position`**: Coordinates `(x, y)` of the opponent's head (updated every step if visible in `sight`).
   - **`tail_position`**: Coordinates `(x, y)` of the opponent's tail (calculated based on movement patterns).
   - **`last_positions`**: A list of the last 10 positions `(x, y)` the opponent's head occupied (for historical movement analysis).

2. **Behavioural Analysis**
   - **`moving_towards_food`**: Boolean value indicating whether the opponent is prioritising food based on its observed trajectory.
   - **`self_traverse`**: Assumed state of the opponent's wrapping ability (`True` or `False`), dynamically updated.

3. **Food Interaction**
   - **`target_food`**: Coordinates `(x, y)` of the food the opponent is likely targeting (if detectable from its trajectory).

4. **Prediction**
   - **`predicted_next_move`**: The expected next position `(x, y)` of the opponent's head based on current observations and inferred strategy.

---
