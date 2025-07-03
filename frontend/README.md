# Frontend 
## Development
This will start the app on http://localhost:5173. The admin view is available on http://localhost:5173/admin/

```sh
npm install
npm run dev
```

Type-Check, Compile and Minify for Production

```sh
npm run build
```

## Lint and format

```sh
npm run lint
npm run format
```

## Tests

```sh
npx playwright install --with-deps
npm run test

# playwright test ui
npm run testui
```
## Design
Adjust your design assets. The design assets located [here](./src/assets/)
```
assistant.svg # used for chatbot-avatar
user.png # used for use-avatar
tagline.svg # Optional: Marcel logo, used in information modal
umr.svg # Optional: University logo, used in information modal
```
Icon sources:

- Feather: https://github.com/feathericons/feather
- Flowbite: https://flowbite.com/icons/
