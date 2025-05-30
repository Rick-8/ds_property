
# DS Property Maintenance — The Ultimate Full-Stack E-Commerce Solution for Property Services

Welcome to **DS Property Maintenance**, a cutting-edge, full-stack web application designed to revolutionize the way property services and maintenance companies manage, market, and monetize their offerings online.

Built with **Django** and powered by seamless **Stripe payment integration**, this platform merges robust backend functionality with an intuitive, responsive frontend to deliver an unparalleled user experience. Whether you're a property owner seeking tailored maintenance packages or a business aiming to streamline service management and sales, DS Property Maintenance is engineered to meet every need with speed, security, and style.

With a comprehensive **role-based authentication system**, dynamic quoting tools, and multiple sub-company storefronts, DS Property Maintenance stands out as a sophisticated yet accessible digital storefront — bringing professionalism, efficiency, and modern e-commerce directly to your fingertips.

---

## 2. Overview / Introduction

**DS Property Maintenance** is a versatile full-stack web application crafted to transform traditional property service management into a seamless online experience. Leveraging the power of **Django’s** robust backend combined with a clean, modern UI built with **Materialize CSS**, this project delivers an integrated platform where users can browse products, subscribe to customizable maintenance packages, and request personalized quotes — all in one place.

Designed with scalability and user-centricity in mind, the application caters to multiple sub-brands — Border 2 Border and Splash Zone Pools — each with unique product lines, yet united under a single, cohesive brand. The app also incorporates secure authentication, role-based permissions, and dynamic payment processing via Stripe, ensuring both customers and administrators enjoy smooth, trustworthy interactions.

---

## 3. User Experience (UX)

At the heart of **DS Property Maintenance** lies a commitment to intuitive, responsive, and engaging user experiences. From the initial wireframes to the final UI polish, every element has been meticulously designed to meet the needs of diverse user groups:

- **Target Audience:** Property owners, maintenance professionals, and product buyers seeking reliable, easy-to-navigate online service solutions.
- **User Goals:** Quick access to product/service information, effortless quote requests, secure checkout, and personalized account management.
- **Business Goals:** Increase conversions through optimized UX, streamline service management for administrators, and foster brand loyalty with tailored subscription packages.

The website architecture supports clear, logical navigation with dedicated landing pages for each sub-brand, a consistent header and footer, and a mobile-first responsive design ensuring flawless usability across all devices.

---

## 4. Features

DS Property Maintenance offers a comprehensive suite of features engineered for efficiency, security, and engagement:

- **User Authentication & Role-Based Access:** Secure sign-up and login powered by Django Allauth, with distinct user roles (admin, customer) dictating access levels.
- **Stripe Payment Integration:** Supports both one-time product purchases and monthly subscription packages with dynamic pricing.
- **Dynamic Quote Generation:** Customers can request tailored quotes including detailed parts, labor, tax calculations, and total costs.
- **Multi-Brand Management:** Seamless navigation between Border 2 Border and Splash Zone Pools product/service catalogs under one parent brand.
- **Responsive Design:** Fully adaptive layouts optimized for desktops, tablets, and mobile devices using Materialize CSS.
- **SEO & Marketing Tools:** Meta tags, sitemap, and email subscription forms built in to boost online visibility and customer engagement.
- **Admin Dashboard:** Efficient backend interfaces for managing products, services, customers, and orders.

---


3. User Experience (UX)
- Strategy
Target audience

User goals

Business goals

- Scope
Features list (briefly mentioned)

- Structure
Site architecture

Navigation flow

User types (e.g. Admin, Customer)

- Skeleton
Wireframes (desktop and mobile)

UI mockups (if available)

- Surface
Color scheme

Typography

Branding

4. Features
List and describe key features, e.g.:

User Authentication (Django Allauth)

Role-based access (admin/customer)

Stripe Payment Integration (subscriptions & one-time checkout)

Property/service/product management

Responsive design

Quote generation (for service packages)

SEO enhancements

Marketing tools (e.g., email subscriptions, promotional banners)

5. Future Features
Any features you would implement given more time

Optional stretch goals

6. Technologies Used
Frontend: HTML5, CSS3, JavaScript, Materialize CSS

Backend: Python, Django

Authentication: Django Allauth

Payments: Stripe

Database: SQLite / PostgreSQL (depending on deployment)

Deployment: Heroku / Render / AWS (specify)

Version Control: Git, GitHub

7. Testing
Manual testing scenarios

Automated tests (if any)

Lighthouse scores (accessibility, performance, SEO)

User feedback (optional)

8. Deployment
Steps taken to deploy the project (with Heroku, Render, etc.)

Environment variables

How to clone & run locally

9. Database Models
List all key models (User, Profile, Property, Product, Quote, etc.)

Include brief descriptions and relationships

10. Marketing and SEO
Techniques implemented (e.g., meta tags, social sharing, Google Analytics)

Any email marketing integration

Sitemap, robots.txt

11. Security
Measures taken for secure authentication

Data validation and sanitization

HTTPS/SSL enforcement

Permissions and access control

12. Credits
Acknowledge any third-party libraries, icons, tutorials, or collaborators

13. Business Model / E-Commerce Rationale
Explain the commercial approach

Subscription logic (for DS Property Maintenance)

Traditional e-commerce model (Border 2 Border, Splash Zone Pools)

14. Screenshots / Demo
Provide screenshots or a walkthrough video

GIFs for key interactions (optional)

15. Bugs / Known Issues
Any unresolved bugs or limitations

16. Credits & Acknowledgements
Inspiration sources
https://www.remove.bg/ - creating clear backgrounds for images

Code Institute (if applicable)

Tutors or mentors

17. Contact Information
Your professional contact details or portfolio

# Project Update: Resolution of Critical Software Bugs and Implementation of Subscription Features

---

This report outlines the successful resolution of several critical bugs and the subsequent implementation of key features related to property management and service agreement display within the `ds_property` application. These efforts have significantly enhanced the application's stability, functionality, and user experience.

---

## Identified Bugs and Remediation Strategies

The following issues were identified and addressed:

1.  **Initial Bug: `SyntaxError: expected ':', got 'indent'`**
    * **Description:** An initial syntax error, primarily caused by incorrect indentation within the Python codebase, prevented the application from running. Python's strict indentation rules are fundamental for defining code blocks correctly.
    * **Resolution:** The problematic indentation in the affected Python file was precisely corrected to adhere to Python's syntax requirements, restoring code executability.

2.  **Bug: `TypeError: ServiceAgreement() got unexpected keyword arguments`**
    * **Description:** When attempting to create `ServiceAgreement` objects, a `TypeError` was encountered. This indicated that specific keyword arguments (e.g., `start_date`, `status`, `stripe_customer_id`, `stripe_price_id`, `amount_paid`) were being passed to the `ServiceAgreement.objects.create()` method but were not defined as fields within the `ServiceAgreement` model in `memberships/models.py`.
    * **Resolution:** The `ServiceAgreement` model in `memberships/models.py` was updated to include these missing fields (`start_date`, `status`, `stripe_customer_id`, `stripe_price_id`, and `amount_paid`) with their appropriate data types. Subsequently, Django database migrations (`python manage.py makemigrations` and `python manage.py migrate`) were executed to apply these schema changes to the underlying database.

3.  **Bug: `NoReverseMatch` for 'property_detail' URL**
    * **Description:** The `property_list.html` template generated a `NoReverseMatch` error because it contained a reference to a URL pattern named `'property_detail'` that did not exist in the project's URL configuration. A separate "property detail" page was also re-evaluated and deemed unnecessary for the current scope.
    * **Resolution:** The problematic link referencing the non-existent `property_detail` URL was removed from the `accounts/templates/account/property_list.html` template, effectively resolving the `NoReverseMatch` error.

4.  **Missing Property Action Buttons (Add, Edit, Delete)**
    * **Description:** Following previous template modifications, the essential "Add," "Edit," and "Delete" buttons for property management were inadvertently removed from the `property_list.html` display. Although the backend views for these actions (`add_property`, `edit_property`, `delete_property`) were in place, the front-end links were absent.
    * **Resolution:** The `accounts/templates/account/property_list.html` template was updated to re-incorporate these critical buttons. This included a prominent "Add New Property" button and, for each listed property, distinct "Edit" and "Delete" buttons. The "Delete" functionality was implemented using a secure POST request via an HTML form for data integrity.

5.  **Incorrect "Inactive Packages" Display on Property List**
    * **Description:** Properties on the `property_list.html` page consistently showed "Inactive" package statuses, despite corresponding active service agreements existing. This issue arose because the `list_properties` view was using an outdated, inefficient manual loop to determine agreement status, while the template was designed to rely on a `property.active_agreements` attribute populated by Django's `prefetch_related` method, which was missing from the view.
    * **Resolution:** The `list_properties` view in `accounts/views.py` was refactored to incorporate Django's **`prefetch_related`** method. A `Prefetch` object was defined to efficiently fetch only active `ServiceAgreement` instances (and their related `ServicePackage` details) and attach them directly to each `Property` object as `active_agreements`. The redundant manual loop for status determination was subsequently removed from the view.

---

## Conclusion

All identified software bugs have been successfully resolved, resulting in a stable and fully functional property listing page. The implementation of efficient data fetching mechanisms, coupled with the re-establishment of essential property management actions, significantly enhances both the reliability and user experience of the `ds_property` application.



## credits 

https://lottiefiles.com/ - payment animations