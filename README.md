# KenPy

Mod manager for the game Kenshi.

I personally find the default Kenshi mod manager to be unpleasant to use, especially when you have more than 20 mods downloaded.\
That's why I created this tool, primarily for my own use, but you're more than welcome to try it out.

If you bought Kenshi via Steam then KenPy should be able to find it by itself. Otherwise, you will have to select the Kenshi folder the first time you run this mod manager.

Notable features
1) **Sort**\
The Sort will try to preserve your order of active mods but if a mod requires another mod that is loaded later, the required mod will be moved up in the load order.
- If a mod is in active list and is missing a prerequisite it will be "red".
- If it has prerequisite but it's loaded later it will be "orange".
2) **Load Modlist from a Save**\
You can select a save file and KenPy will try to load the mods from it and set the active modlist accordingly.

\
I also tried to make it multiplatform so it may run on Linux or Mac devices.\
But I did not test it. On Windows 11 (my machine) it works fine.

At its current stage the GUI is not polished and is missing some small QoL features.\
You can check the TODO list.


**DISCLAIMER:**\
_The UI layout and name are inspired by RimPy for Rimworld but other than that it is in no way or form associated with it._

---
**FOR DEVELOPERS**\
If you are a developer or just want to tinker with it.\
I developed this with Python 3.12.5.

The GUI is written with **tkinter** which I know does not produce great looking GUI but at least the project is super simple to setup and run.

The only third party package is **pillow** for image handling.\
And I used **pyinstaller** to create the executable file.

I am also aware that the quality of the code isn't great and it deserves a proper rewrite.
