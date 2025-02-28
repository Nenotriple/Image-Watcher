<h1 align="center"><img src="https://github.com/user-attachments/assets/509b56a3-b95f-4d2d-931f-b40edf8c2ce2" alt="icon" width="50"> Image-Watcher</h1>
<p align="center">A simple tool to monitor and manage images in a directory with helpful features</p>
<p align="center"><img src="https://github.com/user-attachments/assets/f47f6670-9698-4635-b855-c89a0f6482b7" alt="cover"></p>


## [💾 Download Latest Release](https://github.com/Nenotriple/Image-Watcher/releases)


## 📝 Usage
- Download the latest release.
- Launch the application and select a directory to monitor/manage.
- Browse images by navigating with the arrow keys or using provided controls.
- Filter and search images via PNG metadata.
  - Currently only stable-diffusion-webui-forge/stable-diffusion-webui are supported/tested.
- Saved images will be moved to a local folder `Saved Images`.
- An image database will be created in the selected directory to handle metadata.


## 💡 Tips / Features
- Live Updates: Automatically detects new images.
  - Stay on Index #1 to view new images as they're added.
- Easily switch between the latest image and last viewed image using the quick-swap button. `⤸/⤹`
- Quick Actions: Delete *(Del)* or move *(Ins)* images with keyboard shortcuts.
- PNG Metadata: Display PNG metadata such as pos/neg prompt, and other settings.
- Filter: Use the search bar to filter images based on metadata.
  - Filter images and use the `Move All...` command to move all filtered images.
  - Filtering supports advanced operators, see the *Filter usage and syntax* section below for more info.
- Export Metadata: Batch or single export of PNG metadata to text files.


<details>
<summary><h2>🔍 Filter usage and syntax...</h2></summary>

### Usage:
- Use the 'Search' menu and select a filter type(s).
- Enter keywords based on the selected type(s).
- Press 'Enter' to apply the filter.
- Use the 'Clear' button to reset filters.
- Use the 'Refresh' button to update the database.
- Live Mode is disabled when filters are active.

### Operators:
Quick explanation: `AND` is `space`, `OR` is `~`, `NOT` is `-`, use quotes for exact phrases.

- **AND**: Spaces are treated as operators.
  - `mountain lake` and `"mountain lake"` are treated differently.
  - Match *"mountain" **AND** "lake"* vs matching *"mountain lake"* exactly.
 ---
- **OR**: Use `~` to match either term: `mountain ~ lake`
  - Show either *"mountain"* **OR** *"lake"*.
---
- **NOT**: Prefix with `-` to exclude that term: `sunset -beach`
  - Match with *"sunset"* but **NOT** *"beach"*
---
- **Quotes**: Use to match exact phrases: `"mountain lake"`
  - Match *"mountain lake"* as a single term.
---
- Use a Mix of **AND**, **OR**, **NOT**, and **Quotes**:
  - `"mountain ~ lake" sunset -beach`
    - Show *"mountain"* **OR** *"lake"* at sunset but **NOT** *"beach"*.
  - `-"mountain ~ lake" sunset beach`
    - **NOT** images of *"mountain"* **OR** *"lake"* at *"sunset"* **AND** *""beach"*.

</details>


## 🔧 Python Install/Setup
1. Clone the repository: `git clone https://github.com/Nenotriple/Image-Watcher.git`
2. Launch the app using `Start.bat`
3. When prompted, install the required dependencies.
4. The app will launch automatically after installation.
5. Edit the `Start.bat` `FAST_START` variable to `TRUE` to instantly launch the app.
