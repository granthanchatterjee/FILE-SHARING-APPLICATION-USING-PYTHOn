# FILE SHARING APPLICATION USING PYTHON

## Overview

The File Sharing Application is an application developed using Python and Flask that enables users to upload, share, and download files seamlessly. This application simplifies file sharing by generating a unique batch ID for every upload session and creating a QR code that links to the files. Users can share this QR code with others, allowing them to access and download the files effortlessly.

## Code Working

### Database Initialization

The `init_db` function sets up the application's database by creating a table called `files` if it does not already exist. This table stores an ID (a unique identifier for each file), the filename, and a batch ID that groups files uploaded in the same session. This organized structure makes it easy to retrieve and manage files.

### Homepage Display

The `index` function is responsible for rendering the main webpage where users can upload files. The page includes an interactive form that allows users to select multiple files, preview their selections, and remove any unwanted files. JavaScript is used to validate the input and ensure that users do not submit empty uploads. Once the form is submitted, users are redirected to a page displaying the uploaded files along with a corresponding QR code.

### Handling File Uploads

The `upload_file` function processes the files submitted through the upload form. It retrieves the selected files, saves them in the upload directory, and generates a unique batch ID for the session. The filenames along with the batch ID are then stored in the database. After saving the files, this function calls the `generate_qr_code` function to create a QR code that links to the download page for that batch, and finally redirects the user to the sender page.

### Generating QR Codes

The `generate_qr_code` function creates a QR code for each batch of files. It takes the batch ID and generates a QR code containing a URL that points to the file download page. The QR code is saved as an image in the static directory and is displayed on the sender’s page, making it easy for users to share the download link.

### Managing Uploaded Files

The sender function allows users to view and manage the files they have uploaded. When a user accesses the sender page with a specific batch ID, the function retrieves all files associated with that batch from the database and displays them. This page also offers options to download individual files or add additional files to the same batch. If more files are uploaded, they are added to the batch, and the database is updated accordingly.

### Retrieving And Downloading Files

The receiver function handles the retrieval and downloading of files. When a user scans the QR code or visits the shared link, the function fetches all files associated with the given batch ID from the database and displays them on a download page. Users can select individual files for download, or choose to download all files in the batch as a ZIP archive. The `download_file` function facilitates individual file downloads, while the `download_multiple` function creates a ZIP archive for multiple file downloads, streamlining the process for the user.

## Screenshots

- **In browser, this page opens:**
![image](https://github.com/user-attachments/assets/f62295f4-a66b-453f-8e34-32f7bc550f33)



- **After adding 2 files:**
![image](https://github.com/user-attachments/assets/ece252b3-44e0-4413-ba69-ef2caa714f06)

  

- **After clicking Upload All Files:**
![image](https://github.com/user-attachments/assets/874f37b8-0d4b-4dfe-bca5-ad3f2314f622)

  

- **In receiver’s side after either scanning the QR code or clicking the link:**
![image](https://github.com/user-attachments/assets/a4bb33aa-7877-4cd9-89be-48fd12c9a905)
