import ollama
import json

hp = 10
inventory = []
isAlive = True

#settings and options
try:
    with open("settings.json", "r") as file:
        settings = json.load(file)
        model = settings["model"]
        options = settings["options"]
except:
    model="qwen3.5:4b"
    options = {}



#LLM tool call functions
def debug():
    """
    This is a debug function for the user to see llm details and info such as context, messages, etc. Use when player or user askes to debug.
    """
    print("Memory length: " + str(len(memory)))
def healHp(value):
    """
    Player takes damage and loses hp and returns their new hp.
    Arg: Heal value
    """
    global hp
    hp += int(value)
    return str(hp)
def loseHp(value):
    """
    Player takes damage and loses hp and returns their new hp.
    Arg: Amount of hp lost
    """
    global hp
    hp -= int(value)
    return str(hp)
def getHp():
    """
    Get the player's hp as a string."
    """
    return str(hp)
def getInventory():
    """
    Get the player's inventory
    """
    return inventory
def addToInventory(item):
    """
    Add an item to the players inventory
    Args: A item name, as a string
    """
    global inventory
    inventory.append(item)
    return inventory
def removeFromInventory(item):
    """
    Remove an item from players inventory
    Args: A item name, as a string, item name must match exactly to remove
    """
    global inventory
    if("item" in inventory):
        inventory.remove(item)
        return inventory
    else:
        return item + " not found in Inventory. Make sure item string is exact: " + str(inventory)
def playerDies():
    """
    Kills the player, so only run when the player dies. This will terminate the session.
    """
    global isAlive
    isAlive = False
    print("YOU HAVE DIED!")

tools = [
    healHp, loseHp, getHp, getInventory, addToInventory, removeFromInventory, playerDies, debug
]
funcMap = {
    "debug": debug,
    "healHp": healHp,
    "loseHp": loseHp,
    "getHp": getHp,
    "getInventory": getInventory,
    "addToInventory": addToInventory,
    "removeFromInventory": removeFromInventory,
    "playerDies": playerDies
}

#initial LLM setup
systemRole = "You are a story narrator game master for a choose your own story adventure game. Next, start off the adventure with a message to the player."
memory = [{'role': 'system', 'content': systemRole}]

response = ollama.chat(
    model=model,
    messages=memory
)

memory.append({
    'role': 'assistant',
    'content': response['message']['content']
})

print(response['message']['content'])

#Main game loop

while(isAlive):
    prompt = input("---------------------------------\nWhat will you do: ")

    memory.append({
        'role': 'user',
        'content': prompt
    })
    
    response = ollama.chat(
        model=model,
        messages=memory,
        tools=tools,
        options=options
    )

    memory.append({
        'role': 'assistant',
        'content': response['message']['content']
    })

    if response.message.tool_calls:
        for tc in response.message.tool_calls:
            if tc.function.name in funcMap:
                print(f"Calling {tc.function.name} with arguments {tc.function.arguments}")
                result = funcMap[tc.function.name](**tc.function.arguments)
                print(f"Result: {result}")

                # add the tool result to the messages
                memory.append({'role': 'tool', 'tool_name': tc.function.name, 'content': str(result)})

        response = ollama.chat(
            model=model,
            messages=memory,
            tools=tools,
            options=options
        )
        memory.append({
            'role': 'assistant',
            'content': response['message']['content']
        })

    print(response['message']['content'])
    print(response['message'].get('tool_calls'))
