import ollama
import json

hp = 10
inventory = []
isAlive = True

#settings and options
model="qwen3.5:4b"
options = {}
contextSize = 16384
contextUsed = 0
try:
    with open("settings.json", "r") as file:
        settings = json.load(file)
        model = settings["model"]
        options = settings["options"]
        contextSize = settings["options"]["num_ctx"]
except:
    pass

#LLM tool call functions
def debug():
    """
    This is a debug function for the user to see llm details and info such as context, messages, etc. Use when player or user askes to debug.
    """
    print("Memory length: " + str(len(memory)))
    print("Context length: " + str(contextUsed) + "(" + str(contextUsed/contextSize) + ")")
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
    #basic user prompt for input
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
    print("---------------------------------\n" + response['message']['content'])

    #handle tool calls
    while(response.message.tool_calls):
        print("#####Tool call debug#####")
        for tc in response.message.tool_calls:
            if tc.function.name in funcMap:
                print(f"Calling {tc.function.name} with arguments {tc.function.arguments}")
                result = funcMap[tc.function.name](**tc.function.arguments)
                print(f"Result: {result}")

                # add the tool result to the messages
                memory.append({'role': 'tool', 'tool_name': tc.function.name, 'content': str(result)})
        print("#########################")

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

    #handle context management by checking how much context is used up, and if over 90% is used, we summarize the entire convo to reduce context
    contextUsed = response.get("prompt_eval_count", 0)
    usage = contextUsed / contextSize
    if usage >= 0.9:
        # Keep the original system prompt and the last 4 messages for recent context
        systemMessage = memory[0]
        recent = memory[-4:]
        old = memory[1:-4]
        if old:
            print("*****Summarized and compressed session memory.*****")
            # Instructions for the summarization model
            summary_prompt = [
                {
                    "role": "system",
                    "content": """
                        You are a memory manager for a story adventure game. Summarize the conversation into a compact memory.
                        Keep any important details or events that you think will be needed.
                        Do not invent information.
                        Write the summary in a way that allows another AI to continue the story seamlessly.
                    """
                },
                {
                    "role": "user",
                    "content": json.dumps(old)
                }
            ]
            #get the summary and rebuild memory
            response = ollama.chat(
                model=model,
                messages=summary_prompt,
                options=options
            )
            summary = response['message']['content']
            memory = [
                systemMessage,
                {
                    "role": "system",
                    "content": "PREVIOUS STORY MEMORY:\n" + summary
                }
            ] + recent
