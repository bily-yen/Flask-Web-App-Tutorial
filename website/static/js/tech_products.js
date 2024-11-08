let cart = [];
let hpProducts = [];
let epsonProducts = [];
let ricohProducts = [];
let canonProducts = [];

// Fetch HP scanners
async function fetchHPScanners() {
    try {
        const response = await fetch('/api/hp-scanners');
        hpProducts = await response.json();
        displayHPScanners(hpProducts);
    } catch (error) {
        console.error('Error fetching HP scanners:', error);
    }
}

// Fetch Epson scanners
async function fetchEpsonScanners() {
    try {
        const response = await fetch('/api/epson-scanners');
        epsonProducts = await response.json();
        displayEpsonScanners(epsonProducts);
    } catch (error) {
        console.error('Error fetching Epson scanners:', error);
    }
}

// Fetch Ricoh scanners
async function fetchRicohScanners() {
    try {
        const response = await fetch('/api/ricoh-scanners');
        ricohProducts = await response.json();
        displayRicohScanners(ricohProducts);
    } catch (error) {
        console.error('Error fetching Ricoh scanners:', error);
    }
}

// Fetch Canon scanners
async function fetchCanonScanners() {
    try {
        const response = await fetch('/api/canon-scanners');
        canonProducts = await response.json();
        displayCanonScanners(canonProducts);
    } catch (error) {
        console.error('Error fetching Canon scanners:', error);
    }
}

// Display HP scanners
function displayHPScanners(products) {
    const hpProductContainer = document.getElementById('hp-scanner-section');
    hpProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'hp')).join('');
}

// Display Epson scanners
function displayEpsonScanners(products) {
    const epsonProductContainer = document.getElementById('epson-scanner-section');
    epsonProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'epson')).join('');
}

// Display Ricoh scanners
function displayRicohScanners(products) {
    const ricohProductContainer = document.getElementById('ricoh-scanner-section');
    ricohProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'ricoh')).join('');
}

// Display Canon scanners
function displayCanonScanners(products) {
    const canonProductContainer = document.getElementById('canon-scanner-section');
    canonProductContainer.innerHTML = products.map((item, index) => createProductHTML(item, index, 'canon')).join('');
}

// Create HTML for a product
function createProductHTML(item, index, brand) {
    const { image, name, price } = item;
    const imgSrc = image ? `/static/${image}` : '/static/SPAPHOTOS/placeholder-image.png';

    return `
        <div class='box'>
            <div class='img-box'>
                <img class='images' src='${imgSrc}' alt='${name}' />
            </div>
            <div class='bottom'>
                <p>${name}</p>
                <h2>Ksh ${price}.00</h2>
                <div class='inputs'>
                    <div class='inputbox'>
                        <label for="quantity-${brand}-${index}" style="font-weight: bold;font-size:16px; margin-right: 5px;">Quantity:</label>
                        <input 
                            type="number" 
                            id="quantity-${brand}-${index}" 
                            min="1" 
                            value="1" 
                            placeholder="1" 
                            style="width: 50px; border: 2px solid #ccc; padding: 5px; border-radius: 5px;" 
                            title="Select the quantity you want to order"
                        />
                    </div>
                </div>
                <button onclick='addToCart("${brand}", ${index})'>Add to cart</button>
            </div>
        </div>
    `;
}

// Add item to cart
function addToCart(brand, index) {
    const quantityInput = document.getElementById(`quantity-${brand}-${index}`);
    const quantity = parseInt(quantityInput.value, 10) || 1;

    let productsArray;
    switch (brand) {
        case 'hp':
            productsArray = hpProducts;
            break;
        case 'epson':
            productsArray = epsonProducts;
            break;
        case 'ricoh':
            productsArray = ricohProducts;
            break;
        case 'canon':
            productsArray = canonProducts;
            break;
        default:
            return;
    }

    const existingProductIndex = cart.findIndex(item => item.id === productsArray[index].id);
    if (existingProductIndex > -1) {
        cart[existingProductIndex].quantity += quantity;
    } else {
        cart.push({ ...productsArray[index], quantity });
    }

    displayCart();
}

// Remove item from cart
function removeFromCart(index) {
    cart.splice(index, 1);
    displayCart();
}

// Display cart
function displayCart() {
    const cartItemContainer = document.getElementById('cartItem');
    const countElement = document.getElementById('count');
    const totalElement = document.getElementById('total');

    if (cart.length === 0) {
        cartItemContainer.innerHTML = 'Your cart is empty';
        countElement.textContent = '0';
        totalElement.textContent = 'Ksh 0.00';
        return;
    }

    cartItemContainer.innerHTML = cart.map((item, index) => createCartItemHTML(item, index)).join('');
    countElement.textContent = cart.length;
    totalElement.textContent = `Ksh ${calculateTotal().toFixed(2)}`;
}

// Create HTML for cart item
function createCartItemHTML(item, index) {
    return `
        <div class="cart-item">
            <p>${item.name} (Quantity: ${item.quantity})</p>
            <p>Ksh ${item.price}.00</p>
            <p>Total: Ksh ${(item.price * item.quantity).toFixed(2)}</p>
            <button class="remove-button" onclick="removeFromCart(${index})">✖</button>
        </div>
    `;
}

// Calculate total
function calculateTotal() {
    return cart.reduce((acc, item) => acc + item.price * item.quantity, 0);
}

// Call fetch functions on page load
fetchHPScanners();
fetchEpsonScanners();
fetchRicohScanners();
fetchCanonScanners();