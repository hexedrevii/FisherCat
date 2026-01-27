# FisherCat!

Discord bot all about fishing :3

We have, fish... and... rods!

# Instructions
The program uses Environment Variables to pull data, keeping it safe and sound...

So far, we have:
```env
FISHER_TOKEN    # This is the token for the bot.
FISHER_DATABASE # This is the path for the .db file (SQLite3)
```

The program will look in the root of the folder for a `.env` file.

Create a `.env` file in the root of the folder:
```env
FISHER_TOKEN=mycooltoken
FISHER_DATABASE=C:\Users\CoolPerson\Documents\fishy.db
```
The file must not have spaces between the `=` signs, and the strings must NOT have `"`

Once you have that set up, and python installed WITH pip, you can run the following commands to actually run the program:

```bash
python -m venv myenv # Create an environment to not clog your actual computer.

# This step varies on OS and shell installed, if you have Windows with Powershell you can just run this.
.\env\Scripts\Activate.ps1 # Alternatively: activate.bat if you *still* use batch.

pip install -r requirements.txt # This installs all the required dependencies into the environment.

python .\main.py # Run the program!
```
