import React from 'react';
import ReactDOM from "react-dom";
import SupportForm  from './components/SupportForm';

const rootContainer = document.getElementById("zenodo-rdm-support-root");
const domContainer = document.getElementById("zenodo-rdm-support-config");

const categories = JSON.parse(domContainer.dataset.categories);
const user = JSON.parse(domContainer.dataset.user)
const systemInfo = JSON.parse(domContainer.dataset.systemInfo);
const browser = systemInfo.browser;
const platform = systemInfo.platform;
const maxFileSize = parseInt(domContainer.dataset.maxFileSize);
const descriptionMaxLength = parseInt(domContainer.dataset.descriptionMaxLength);
const descriptionMinLength = parseInt(domContainer.dataset.descriptionMinLength);
const apiEndpoint = domContainer.dataset.apiEndpoint;

ReactDOM.render(
    <SupportForm
        userMail={user.email}
        name={user.full_name}
        isUserAuthenticated={Boolean(user)}
        categories={categories}
        userBrowser={browser}
        userPlatform={platform}
        maxFileSize={maxFileSize}
        descriptionMaxLength={descriptionMaxLength}
        descriptionMinLength={descriptionMinLength}
        apiEndpoint={apiEndpoint}
    >
    </SupportForm>,
    rootContainer
);