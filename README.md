# <span style="color:gold">DS Property Management</span> 

---

## Table of Contents

- [Project Overview](#project-overview)
- [Business Model & Purpose](#business-model--purpose)
- [Key Features](#key-features)
- [User Stories](#user-stories)
- [UX Design & Accessibility](#ux-design--accessibility)
- [Data Model & Schema](#data-model--schema)
- [Technologies Used](#technologies-used)
- [App Structure & File Layout](#app-structure--file-layout)
- [Authentication & Authorization](#authentication--authorization)
- [Payment Integration](#payment-integration)
- [SEO Features](#seo-features)
- [Marketing Features](#marketing-features)
- [Testing](#testing)
- [Manual Testing & User Feedback](#manual-testing--user-feedback)
- [Automated Testing](#automated-testing)
- [Deployment Instructions](#deployment-instructions)
- [Configuration & Environment Variables](#configuration--environment-variables)
- [How to Run Locally](#how-to-run-locally)
- [Known Issues / Limitations](#known-issues--limitations)
- [Future Improvements](#future-improvements)
- [Credits & Attribution](#credits--attribution)
- [Screenshots & Demo](#screenshots--demo)
- [Social Media & Marketing](#social-media--marketing)
- [Plagiarism Statement](#plagiarism-statement)

## Project Overview

## <span style="color:gold">DS Property Maintenance Portal</span>

**A Full-Stack Django E-commerce Solution for Florida Property Owners & Managers**

> *A modern, secure platform for property owners, landlords, and managers to buy services, set up subscriptions, and access expert advice and consultation.*

The DS Property Maintenance Portal is an all-in-one web application designed for anyone who owns or manages residential or commercial property in Florida. Whether you are a homeowner, landlord, or property manager, the platform lets you easily:

- Browse and purchase recurring property maintenance services (via subscriptions)
- Request custom, one-off jobs or quotes
- Access professional advice and consultation on property care
- Manage service contracts, schedules, and payments in a secure, user-friendly environment

With built-in Stripe payment integration, robust authentication, staff/admin dashboards, and advanced marketing and SEO features, the portal delivers a professional, reliable, and efficient solution for property maintenance needs.

---

## <span style="color:gold">Business Model & Purpose</span>

The DS Property Maintenance Portal is built on a service-driven e-commerce model, tailored for property owners, landlords, and property managers in Florida.

**Business Model Overview:**
- The platform features two specialized sub-companies:
  - **Border 2 Border:** The go-to for all outdoor property needs—landscaping, lawn care, gardening, grounds maintenance, fencing, tree work, and any service related to the garden or exterior.
  - **Splash Zone Pools:** Dedicated to pool cleaning, repairs, and maintenance, ensuring sparkling, safe pools year-round.
- Customers can:
  - **Purchase ongoing service packages** (subscriptions) for routine property, garden, and pool care
  - **Request and pay for one-off jobs or custom quotes** as needed
  - **Access professional advice and consultation** for all property, outdoor, and pool questions

**Physical & Digital Integration:**
- The business leverages a hybrid structure—combining digital management with real-world service delivery.  
- **Staff members install the DS Property Maintenance Progressive Web App (PWA)** on their phones or tablets, using it on-the-go for job assignments, schedules, and customer details.
- Staff update job statuses, add notes, and submit customer feedback instantly from their devices, ensuring office teams and customers receive real-time updates on service progress and completion.
- This approach streamlines communication, reduces paperwork, and delivers a seamless experience from booking to job fulfillment and feedback.

**Purpose & Value Proposition:**
- **For customers:**  
  An all-in-one platform to manage properties, purchase services, request help, and track every job—with clear, instant feedback and access to real experts.
- **For the business:**  
  Automates recurring revenue through subscriptions, simplifies bespoke job management, and enhances service quality with real-time feedback and centralized digital oversight.
- **For staff/admin:**  
  Field staff benefit from mobile access to job details and instant feedback submission; admin and support teams can coordinate work, monitor performance, and respond to customer needs faster and more efficiently.

**Why this matters:**  
By connecting property owners and managers with a comprehensive suite of local services—especially for outdoor and pool care—and providing instant feedback via digital tools, DS Property Maintenance ensures properties are maintained to the highest standard with minimal hassle, maximum transparency, and exceptional service quality.





---

## <span style="color:gold">Key Features</span>

DS Property Maintenance Portal is packed with features designed for both efficiency and real-world impact, delivering a seamless experience for property owners, staff, and administrators.

- **Multi-Brand Service Hub:**  
  Unified portal hosting two specialist brands—Border 2 Border (all outdoor and garden work) and Splash Zone Pools (full-service pool care)—each with dedicated product/service pages and workflows.

- **Service Package Subscriptions:**  
  Customers can browse and sign up for customizable, recurring maintenance packages for their property or pool, with automated Stripe-powered monthly billing and secure payment management.

- **One-Off Quotes & Job Requests:**  
  Intuitive quote request system for custom jobs, allowing users to upload photos, describe their needs, receive dynamic, itemized quotes, and approve/pay instantly online.

- **Advice & Consultation Access:**  
  Built-in contact and messaging features for users to seek expert advice or schedule professional consultations with the team.

- **Progressive Web App (PWA) for Staff:**  
  Staff members install the PWA on their smartphones or tablets for on-the-go job management. Staff receive real-time job assignments, update job status instantly, submit notes/photos, and collect customer feedback—all feeding directly into the office dashboard.

- **Role-Based Authentication & Dashboards:**  
  Secure login with Django Allauth, with customized dashboards for customers, staff, and administrators. Each user sees only what they need—no unnecessary clutter or confusion.

- **Job Scheduling & Route Planning:**  
  Powerful admin/staff interfaces for assigning jobs, creating and managing staff routes, and tracking job progress and completion—enabling efficient real-world team management.

- **Real-Time Feedback & Notifications:**  
  Staff and customers receive instant updates about job status changes, feedback submission, or service confirmations via web and push notifications.

- **Seamless Stripe Payment Integration:**  
  Supports both one-time payments for individual jobs/quotes and recurring subscription billing. Payments are secure, PCI-compliant, and handled end-to-end via Stripe.

- **Modern, Responsive Design:**  
  Fully responsive UI built with Materialize CSS, ensuring the platform works beautifully across desktops, tablets, and smartphones.

- **SEO-Optimized & Marketing-Ready:**  
  Built-in meta tags, sitemap, robots.txt, email marketing/newsletter signup, and optional social proof features to support discovery and business growth.

- **Custom Admin Controls:**  
  Administrators can manage users, service agreements, packages, jobs, and feedback with a robust backend interface designed for clarity and speed.

- **Agile & Extensible Architecture:**  
  Built using Django best practices, with a clear app structure, reusable components, and clean, well-documented code—making it easy to add new brands, services, or features as the business grows.

---

**Every feature is designed with both the customer and staff experience in mind—ensuring property owners get the services and support they need, and the business operates smoothly from the office to the field.**


---

## <span style="color:gold">User Stories</span>

Below are the main user stories that guided the development of DS Property Maintenance. Each story is mapped to features/pages that implement the required functionality.

---

### General Users / Customers

- **Registration and Login**
  - *User Story:*  
    As a user, I want to be able to register for an account and log in, so I can access personalized features.
  - *Achieved via:*  
    Django Allauth integration. Users can register, log in, and manage their account securely from the navigation menu.

- **Password Reset**
  - *User Story:*  
    As a user, I want to be able to reset my password if I forget it.
  - *Achieved via:*  
    Password reset flow using Django Allauth (with email confirmation).

- **Browse and View Products/Services**
  - *User Story:*  
    As a user, I want to browse products and view detailed information before making a purchase.
  - *Achieved via:*  
    Main product/service pages for Border 2 Border and Splash Zone Pools, including detailed descriptions, package information, and pricing.

- **Shopping Cart & Checkout**
  - *User Story:*  
    As a customer, I want to add products to a basket and check out securely.
  - *Achieved via:*  
    Shopping basket feature for product purchases, Stripe payment integration for both one-off and subscription-based checkouts.

- **One-off Quotes & Reviews**
  - *User Story:*  
    As a customer, I want to request a custom quote and leave feedback or reviews.
  - *Achieved via:*  
    Quote request form (with image upload and detailed builder), dynamic quote builder for admins, and feedback forms on job/service completion.

- **Responsive Layout**
  - *User Story:*  
    As a user, I want a responsive layout that works on any device.
  - *Achieved via:*  
    Fully responsive design using Materialize CSS and custom media queries; PWA for staff.

- **Order Confirmation and Feedback**
  - *User Story:*  
    As a user, I want to receive confirmation after ordering, and leave feedback.
  - *Achieved via:*  
    Success pages, confirmation emails, and dashboard notifications; feedback modal for job completion.

---

### Admin / Staff / Site Owner

- **Order Management**
  - *User Story:*  
    As a site owner, I want to see a list of all customer orders/requests.
  - *Achieved via:*  
    Admin dashboard listing orders, quotes, and customer details.

- **Product/Service Management**
  - *User Story:*  
    As an admin, I want to create, edit, and delete products or services.
  - *Achieved via:*  
    CRUD admin interface for service packages, products, and agreements.

- **User Role Management**
  - *User Story:*  
    As an admin, I want to manage user roles (e.g., promote to staff/admin).
  - *Achieved via:*  
    Django admin interface and custom role assignments during user creation.

- **Job Scheduling and Assignment**
  - *User Story:*  
    As a staff/admin, I want to assign jobs, track progress, and get instant feedback.
  - *Achieved via:*  
    Job scheduling dashboard, staff PWA (installable on mobile), and real-time feedback forms.

---

### Developer / Technical Stories

- **Deployment**
  - *User Story:*  
    As a developer, I want to deploy the application to a reliable hosting platform.
  - *Achieved via:*  
    The app is cloud-hosted (Heroku/Render), with a documented deployment process.

- **SEO Features**
  - *User Story:*  
    As a developer, I want SEO features implemented to boost discoverability.
  - *Achieved via:*  
    Proper meta tags, sitemap, robots.txt, semantic markup, and consistent URLs.

- **Automated & Manual Testing**
  - *User Story:*  
    As a developer, I want to write tests and ensure the app is robust.
  - *Achieved via:*  
    Manual and (where implemented) automated tests for core features; bug tracking and resolution documented in README.

- **Error Handling**
  - *User Story:*  
    As a developer, I want errors to be gracefully handled and communicated to users.
  - *Achieved via:*  
    User-friendly error messages, success/failure feedback on forms, custom 404 and error pages.

---

Each story above is implemented in live features/pages, and every key acceptance criterion has been met.  
**See the Features section for details and screenshots of these flows.**


---

## UX Design & Accessibility

_Explain your UX approach, wireframes, accessibility considerations, and design._

---

## Data Model & Schema

_Describe your database models and their relationships (with diagrams if possible)._

---

## Technologies Used

_List all technologies, frameworks, libraries, and services used._

---

## App Structure & File Layout

_Explain your folder structure and how the app is organized._

---

## Authentication & Authorization

_Describe how users are authenticated and roles are handled._

---

## Payment Integration

_Describe payment functionality and Stripe integration._

---

## SEO Features

_Detail the SEO measures you have implemented (meta tags, sitemap, robots.txt, etc)._

---

## Marketing Features

_Describe marketing features such as newsletters, social proof, or campaign tools._

---

## Testing

_Overview of your testing approach for the application._

---

## Manual Testing & User Feedback

_Describe manual test cases and user feedback collection._

---

## Automated Testing

_List and describe automated tests (unit, integration, etc)._

---

## Deployment Instructions

_Step-by-step guide to deploy the application._

---

## Configuration & Environment Variables

_Describe the required environment variables and configuration settings._

---

## How to Run Locally

_Instructions for running the project locally for development._

---

## Known Issues / Limitations

_List any known bugs, issues, or limitations._

---

## Future Improvements

_Suggest features and enhancements planned for the future._

---

## Credits & Attribution

_Credit any resources, libraries, tutorials, or collaborators._

---

## Screenshots & Demo

_Include screenshots and/or a link to a live demo._

---

## Social Media & Marketing

_Describe your social media efforts (include screenshots/links as required)._

---

## Plagiarism Statement

_Declare that the project is your own work, with proper attribution as needed._

---

