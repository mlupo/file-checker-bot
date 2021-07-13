from svgelements import SVGText, Path, SVGImage, SVG, Shape, Color, SVGElement
import discord
import os
from dotenv import load_dotenv


def prepFile(file):
    '''this function takes in a file and parses it with the svgelements module'''
    file = SVG().parse(file)
    svg_elements = []
    for i in file.elements():
        if isinstance(i, list):
            # sometimes the svg file contains objects in lists, so we must unpack them
            svg_elements.extend(i)
        else:
            svg_elements.append(i)

    return svg_elements


def errorChecker(path_list):
    '''take the svg elements, and iterate over them to check for various issues'''
    issues = set()
    flags = {
        "image": "It looks like this svg file contains a bitmap image. That is okay if you are prepping this file for the print & cut, but if you are planning to use this for the laser, then it might need to be traced (converted to a vector) first.",
        "text": "This file contains some text. That's not bad on its own, but if our computer does not have your chosen font installed, it will not appear correctly. Consider converting your text to paths.",
        "stroke-width": 'You have a stroke width larger than 0.001". Please note that only strokes sized at 0.001" will cut, and all larger strokes will be engraved by the laser. The print & cut will always cut any stroke of any size.',
        "none": "Congrats, there are no obvious issue that I can see, feel free to convert this file to a pdf for printing, or ask for this file to be reviewed by staff if you want to make sure.",
        "no-cuts": "There doesn't seem to be any stroke lines in this file, meaning that there are no cut lines for the laser OR the print & cut. If that was intentional then carry on, or else you may need to review your file.",  # not implemented
        "tiny-stroke": 'There is a stroke line that is less than 0.001 inches. A line this thin may cut with the print & cut, but will not be recognized by the laser.'}

    for element in path_list:
        if isinstance(element, SVGText):
            issues.add(flags["text"])
        if isinstance(element, Path) or isinstance(element, Shape) or isinstance(element, SVGText):
            if element.stroke_width > 0.095 and element.stroke != Color(None):
                issues.add(flags["stroke-width"])
            if element.stroke_width < 0.092 and element.stroke != Color(None):
                # a stroke line less than 0.092px is probably a mistake
                issues.add(flags["tiny-stroke"])
        if isinstance(element, SVGImage):
            issues.add(flags["image"])

    if len(issues) < 1:
        issues.add(flags["none"])

    return issues

# test = prepFile("SmashingBojo.svg")
# # print(test, file=open('test.txt', 'a'))
# issues = errorChecker(test)
# print(issues)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if 'check' in message.clean_content.lower() and str(message.channel) == "auto-file-checker" and len(message.attachments) == 1:
        if 'svg' in message.attachments[0].filename.lower():
            await message.attachments[0].save("to_parse.svg")
            svg_contents = prepFile("to_parse.svg")
            msg = errorChecker(svg_contents)
            string = ""
            greeting = f"Hi {message.author.mention} I have some notes about your file:"
            for i in msg:
                string += '\n\n' + i
            await message.channel.send(greeting + string)
        else:
            await message.channel.send(f"Hi {message.author.mention} something is not quite right, I wasn't able to check your file.")

client.run(os.getenv('TOKEN'))
