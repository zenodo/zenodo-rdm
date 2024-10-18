import React from "react";
import ReactDOM from "react-dom";
import { CommunityItem } from "./community-item";
import { CommunitySelectionSearch } from "@js/invenio_rdm_records";

const defaultProps = {
  isInitialSubmission: true,
  apiConfigs: {
    allCommunities: {
      initialQueryState: { size: 5, page: 1, sortBy: "newest" },
      searchApi: {
        axios: {
          url: "/api/communities",
          headers: { Accept: "application/vnd.inveniordm.v1+json" },
        },
      },
      appId: "ReactInvenioDeposit.CommunitySelectionSearch.recentCommunities",
      toggleText: "Search in all communities",
    },
    myCommunities: {
      initialQueryState: { size: 5, page: 1, sortBy: "bestmatch" },
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
    autofocus={false}
  />,
  document.getElementById("project-search-menu")
);
