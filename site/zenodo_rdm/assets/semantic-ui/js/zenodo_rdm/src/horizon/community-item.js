import React, { Component } from "react";
import PropTypes from "prop-types";
import {
  List,
  ListItem,
  ListContent,
  ListHeader,
  ListDescription,
} from "semantic-ui-react";

export class CommunityItem extends Component {
  render() {
    const { result } = this.props;
    const {
      metadata: { title, funding },
      links: { self_html: requestLinkSelf },
    } = result;

    const awardAcronym = funding && funding[0]?.award?.acronym;

    return (
      <List className="rel-mt-1">
        <ListItem>
          <ListContent>
            <ListHeader as="a" href={requestLinkSelf}>
              <h4 className="theme-primary-text-direct">{title}</h4>
            </ListHeader>
            <ListDescription>{awardAcronym}</ListDescription>
          </ListContent>
        </ListItem>
      </List>
    );
  }
}

CommunityItem.propTypes = {
  result: PropTypes.object.isRequired,
};
