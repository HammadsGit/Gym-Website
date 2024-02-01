# Initial Design, to now
The site was initially started with plain Bootstrap, without any custom style changes. Cards were used early on to section content on the page, as described in [Page Styling](#page-styling). To make custom styling easier later on, native bootstrap elements were used where possible.

Layout was thought about from the beginning, and due to this, adjustments were made as features were added, and we felt no need to make large changes  to the general layout of the site later on. However, colors and other small details were changed to give the site/brand an identity, and distinguish it from others.

Below is a screenshot of the activities page at commit [`6d153f8`](https://github.com/uol-feps-soc-comp2913-2223s2-classroom/project-squad39/commit/6d153f8d78410b63b74651880e61c471243c0f43) (28th March 2023), and commit [`1a124f5`](https://github.com/uol-feps-soc-comp2913-2223s2-classroom/project-squad39/commit/1a124f5bfda0dbe7832bd0871531eb64af04a538) (26th April 2023), which shows how the general layout has not changed a lot since this page's functionality was completed.

28th March (6d153f8) | 26th April (1a124f5)
:---:|:---:
![28th March](https://dump.hrfee.pw/gymcorp-6d153f8.png) | ![26th April](https://dump.hrfee.pw/gymcorp-1a124f5.png)

# Colors
Most buttons and other similar elements use Bootstrap's native colors, as they blend well with the rest of the site, and changing them would involve the need to introduce a full build process in order to compiles SASS.

The [Open Color Palette](https://yeun.github.io/open-color/) was used to pick colors for the background of pages and cards, and the colors of the logo.

The colors chosen are soft to give the site the same feel as its drawn-style logo, but still provide enough contrast to make elements easily distinguishable.


# Page Styling

The site has a light & dark mode, which are applied base on the Operating System/Browser's preference, which is often set to choose a dark theme in the evening to reduce eye strain. The mode can also be changed through a button on the navigation bar.

Light | Dark
:---:|:---:
![Light](https://dump.hrfee.pw/gymcorp-light.png) | ![Dark](https://dump.hrfee.pw/gymcorp-dark.png)

Cards are heavily used throughout the site to separate differing pieces of content from each other, such as on the activities page, where standard activities and classes are in their own cards. Occasionally they are used in a nested fashion, such as to display an individual class and all its details in a list. At other times, where less separation is needed, a flush list is used, which provides separator bars between list elements, as seen on the "My Bookings" page.

Alongside cards, Bootstrap's breakpoint, grid and column concepts are used in order to determine the size of elements on the page in a way that handles differing display sizes. This can notably be seen on the home page, where most cards are conditionally displayed, and yet still display correctly with any combination of them visible or hidden. On mobile devices, columns are automatically wrapped so that each is legible, as seen below.

Desktop | Mobile
:---:|:---:
![Desktop](https://dump.hrfee.pw/gymcorp-full.png) | ![Mobile](https://dump.hrfee.pw/gymcorp-mobile.png)

# Implementation
Colors are imported as CSS variables from a local copy of Open Color's CSS palette, and then Bootstrap's CSS variables are modified to adjust page styling in a consistent fashion. Where necessary (such as for rounded cards), manual overrides for certain classes are used. All of these changes can be found in [`theme.css`](https://github.com/uol-feps-soc-comp2913-2223s2-classroom/project-squad39/blob/1a124f5bfda0dbe7832bd0871531eb64af04a538/app/static/theme.css).

## Logo
The logo uses the "G" in GymCorp as its central feature, enclosing it in a colored circle and using a contrasting teal color for the letter itself to keep legibility. The "G" is partially covered by a graphic of a running person, which was roughly traced from the [`run-line` icon from RemixIcon](https://remixicon.com/icon/run-line), an open-source icon pack.

Similar to the running person, a pre-existing font wasn't used for the text, instead it was drawn by hand and replicated in a vector graphics software. This was done to give the logo an inviting feel. Its main colour, [Red 5 (#ff6b6b)](https://yeun.github.io/open-color/#red-5), provides good contrast against both light and dark backgrounds.

