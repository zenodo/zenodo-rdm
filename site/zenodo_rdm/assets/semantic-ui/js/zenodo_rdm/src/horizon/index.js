import React from "react";
import ReactDOM from "react-dom";
import { CommunityItem } from "./community-item";
import { CommunitySelectionSearch } from "@js/invenio_rdm_records";

const projectSearchContainer = document.getElementById("project-search-menu");
const isUserAuthenticated = JSON.parse(projectSearchContainer.dataset.isAuthenticated);
const communitySlug = projectSearchContainer.dataset.communitySlug;


const defaultProps = {
  isInitialSubmission: true,
  apiConfigs: {
    allCommunities: {
      initialQueryState: { size: 6, page: 1, sortBy: "newest" },
      searchApi: {
        axios: {
          url: `/api/communities/${communitySlug}/subcommunities`,
          headers: { Accept: "application/vnd.inveniordm.v1+json" },
        },
      },
      appId: "ReactInvenioDeposit.CommunitySelectionSearch.recentCommunities",
      toggleText: "Search in all communities",
    },
    myCommunities: {
      initialQueryState: { size: 6, page: 1, sortBy: "bestmatch" },
      searchApi: {
        axios: {
          url: "/api/user/communities",
          headers: { Accept: "application/vnd.inveniordm.v1+json" },
        },
      },
      appId: "ReactInvenioDeposit.CommunitySelectionSearch.MyCommunities",
      toggleText: "Search in my communities",
    },
  },
};

ReactDOM.render(
  <CommunitySelectionSearch
    apiConfigs={defaultProps.apiConfigs}
    isInitialSubmission={defaultProps.isInitialSubmission}
    CommunityListItem={CommunityItem}
    pagination={false}
    myCommunitiesEnabled={isUserAuthenticated}
    autofocus={false}
  />,
  projectSearchContainer
);
