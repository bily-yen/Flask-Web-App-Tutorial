#!/bin/bash

equipment_items=(
    "printer"
    "computer"
    "scanner"
    "projector"
    "photocopier"
    "laminator"
    "whiteboard"
    "monitor"
    "laptop"
)

for item in "${equipment_items[@]}"; do
    cat <<EOL > "${item}.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${item^} Page</title>
</head>
<body>
    <header>
        <h1>${item^} Page</h1>
    </header>
    <main>
        <p>Details about ${item}.</p>
        <a href="/">Go back</a>
    </main>
    <footer>
        <p>Footer information here.</p>
    </footer>
</body>
</html>
EOL
    echo "Created ${item}.html"
done
