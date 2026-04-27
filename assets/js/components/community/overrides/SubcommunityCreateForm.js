import { i18next } from "@translations/invenio_communities/i18next";
import { Formik } from "formik";
import _get from "lodash/get";
import _isEmpty from "lodash/isEmpty";
import PropTypes from "prop-types";
import React, { Component } from "react";
import {
  AffiliationsSuggestions,
  FieldLabel,
  RadioField,
  SelectField,
  TextField,
  TextAreaField,
  withCancel,
  http,
  RemoteSelectField,
} from "react-invenio-forms";
import {
  Button,
  Divider,
  Form,
  Grid,
  Header,
  Icon,
  Message,
  Segment,
} from "semantic-ui-react";
import { CommunityApi } from "@js/invenio_communities/api";
import { communityErrorSerializer } from "@js/invenio_communities/api/serializers";

class SubcommunityCreateForm extends Component {
  state = {
    error: "",
    hasCommunity: false,
    communities: [],
    organizationsKey: "initial",
    organizationSuggestions: [],
  };

  knownOrganizations = {};

  componentDidMount() {
    withCancel(
      http
        .get("/api/user/communities?sort=newest")
        .then((response) => response.data)
        .then((data) => {
          this.setState({
            communities: data?.hits?.hits
              .filter((item) => !item?.parent?.id)
              .filter((item) => !item?.children?.allow === true)
              .map((item) => ({
                text: item.metadata.title,
                value: item.id,
                key: item.id,
              })),
          });
        })
        .catch((error) => {
          console.error(error);
        })
    );
  }

  componentWillUnmount() {
    this.cancellableCreate && this.cancellableCreate.cancel();
  }

  setGlobalError = (errorMsg) => {
    this.setState({ error: errorMsg });
  };

  serializeOrganizations = (values) => {
    const orgs = values?.metadata?.organizations || [];
    return orgs.map((org) => {
      const orgName = this.knownOrganizations[org];
      return orgName ? { id: org, name: orgName } : { name: org };
    });
  };

  onSubmit = async (values, { setSubmitting, setFieldError }) => {
    setSubmitting(true);
    const client = new CommunityApi();
    const { hasCommunity } = this.state;
    const { community } = this.props;
    const organizations = this.serializeOrganizations(values);
    let payload = {};
    if (hasCommunity) {
      payload = {
        community_id: values["metadata"]["community"],
        payload: {
          project_id: values["metadata"]["project_id"],
        },
      };
    } else {
      payload = {
        community: {
          title: values["metadata"]["title"],
          slug: values["metadata"]["slug"],
          description: values["metadata"]["description"] || null,
          website: values["metadata"]["website"] || null,
          organizations: organizations.length ? organizations : null,
        },
        payload: {
          project_id: values["metadata"]["project_id"],
        },
      };
    }
    this.cancellableCreate = withCancel(
      client.createSubcommunity(community.id, payload)
    );

    try {
      const response = await this.cancellableCreate.promise;
      setSubmitting(false);
      const requestID = response.data.id;
      // TODO It is computed for now because the link contains references to two different entities (request and community), and that's not supported yet by the backend.
      window.location.href = `/communities/${community.slug}/requests/${requestID}`;
    } catch (error) {
      if (error === "UNMOUNTED") return;

      const { errors, message } = communityErrorSerializer(error);

      if (message) {
        this.setGlobalError(
          "The form contains errors or missing fields. Please verify before submitting."
        );
      }

      if (errors) {
        errors.map(({ field, messages }) => {
          // Check if the field is already prefixed with "metadata"
          if (!field.startsWith("metadata")) {
            // Add "metadata" prefix if not already present
            field = `metadata.${field.split(".").pop()}`;
          }
          setFieldError(field, messages[0]);
        });
      }
    }
  };

  render() {
    const { formConfig, canCreateRestricted } = this.props;
    const {
      hasCommunity,
      communities,
      error,
      organizationsKey,
      organizationSuggestions,
    } = this.state;

    return (
      <Formik
        initialValues={{
          access: {
            visibility: "public",
          },
          metadata: {
            slug: "",
            title: "",
            project_id: "",
            description: "",
            website: "",
            organizations: [],
          },
        }}
        onSubmit={this.onSubmit}
      >
        {({ values, isSubmitting, handleSubmit }) => {
          const isAutoFilled = !!values.metadata.project_id;
          const autoFilledHint = isAutoFilled ? (
            <small className="ml-5" style={{ color: "#2185d0" }}>
              <Icon name="magic" size="small" />
              <em>{i18next.t("auto-filled")}</em>
            </small>
          ) : null;
          return (
            <Form onSubmit={handleSubmit} className="communities-creation">
              <Message hidden={error === ""} negative className="flashed">
                <Grid container centered>
                  <Grid.Column mobile={16} tablet={12} computer={8} textAlign="left">
                    <strong>{error}</strong>
                  </Grid.Column>
                </Grid>
              </Message>
              <Grid container centered>
                <Grid.Row>
                  <Grid.Column mobile={16} tablet={12} computer={8} textAlign="center">
                    <Header as="h1" className="rel-mt-2">
                      {i18next.t("Setup your new EU project community")}
                    </Header>
                    <Divider />
                  </Grid.Column>
                </Grid.Row>
                <Grid.Row textAlign="left">
                  <Grid.Column mobile={16} tablet={12} computer={8}>
                    <Segment className="message info visible">
                      <Header as="h5" className="rel-mb-1">
                        {i18next.t("Only for EU-funded projects.")}
                      </Header>
                      {i18next.t(
                        "To setup a new EU project community, you must be affiliated with an EU-funded project (e.g. Horizon 2020, Horizon Europe, Euratom)."
                      )}
                      <Header as="h5" className="rel-mb-1 rel-mt-2">
                        {i18next.t("Institutional email required.")}
                      </Header>
                      {i18next.t(
                        "In order for us to verify the request, your Zenodo account must be using an institutional email address, so that we can verify your institutional affiliation. You can change your email address in "
                      )}
                      <a href="/account/settings/profile">
                        {i18next.t("your profile settings ")}
                      </a>
                      {i18next.t("if that is not the case.")}
                    </Segment>
                    <div className="field">
                      <Form.Field>
                        {i18next.t("Do you already have an existing community?")}
                      </Form.Field>
                      <Form.Group>
                        <RadioField
                          label={i18next.t("Yes")}
                          checked={hasCommunity === true}
                          value={i18next.t("Yes")}
                          onChange={() => {
                            this.setState({ hasCommunity: true });
                          }}
                          fieldPath="metadata.hasCommunity"
                          disabled={_isEmpty(communities)}
                        />
                        <RadioField
                          label={i18next.t("No")}
                          checked={hasCommunity === false}
                          value={i18next.t("No")}
                          onChange={() => {
                            this.setState({ hasCommunity: false });
                          }}
                          fieldPath="metadata.hasCommunity"
                        />
                      </Form.Group>
                    </div>
                    <RemoteSelectField
                      fieldPath="metadata.project_id"
                      id="metadata.project_id"
                      searchQueryParamName="q"
                      placeholder={i18next.t("Search for a project by name")}
                      suggestionAPIUrl="/api/awards"
                      suggestionAPIHeaders={{
                        Accept: "application/vnd.inveniordm.v1+json",
                      }}
                      suggestionAPIQueryParams={{ funders: "00k4n6c32" }}
                      serializeSuggestions={(suggestions) =>
                        suggestions.map((item) => ({
                          text: `${item.title_l10n} ${
                            item.acronym ? ` - (${item.acronym})` : ""
                          } - ${item.number}`,
                          content: (
                            <Header
                              content={`${item.title_l10n}${
                                item.acronym ? ` - (${item.acronym})` : ""
                              }`}
                              subheader={item.number}
                            />
                          ),
                          value: item.id,
                          key: item.id,
                          acronym: item.acronym,
                          title: item.title_l10n,
                          short_description: item.short_description_l10n,
                          website:
                            item.website ||
                            item.identifiers.find((id) => id.scheme === "url")
                              ?.identifier ||
                            "",
                          organizations: item.organizations || [],
                        }))
                      }
                      onValueChange={({ data, formikProps }) => {
                        let selectedProject = data.options.find(
                          (option) => option.value === data.value
                        );
                        // Defer blur past SUI Dropdown's internal auto-refocus
                        // of the search input after a selection.
                        setTimeout(() => {
                          const input = document.getElementById("metadata.project_id");
                          input && input.blur();
                        }, 0);
                        if (selectedProject) {
                          formikProps.form.setFieldValue(
                            formikProps.fieldPath,
                            selectedProject.key
                          );
                          formikProps.form.setFieldValue(
                            "metadata.title",
                            selectedProject.title
                          );
                          if (selectedProject.acronym) {
                            formikProps.form.setFieldValue(
                              "metadata.slug",
                              selectedProject.acronym.toLowerCase()
                            );
                          }
                          formikProps.form.setFieldValue(
                            "metadata.description",
                            selectedProject.short_description
                          );
                          formikProps.form.setFieldValue(
                            "metadata.website",
                            selectedProject.website
                          );
                          const orgNames = (selectedProject.organizations || [])
                            .map((org) => org.organization)
                            .filter(Boolean);
                          formikProps.form.setFieldValue(
                            "metadata.organizations",
                            orgNames
                          );
                          this.setState({
                            organizationsKey: selectedProject.key,
                            organizationSuggestions: orgNames.map((name) => ({ name })),
                          });
                        } else {
                          formikProps.form.setFieldValue("metadata.project_id", "");
                          formikProps.form.setFieldValue("metadata.title", "");
                          formikProps.form.setFieldValue("metadata.slug", "");
                          formikProps.form.setFieldValue("metadata.description", "");
                          formikProps.form.setFieldValue("metadata.website", "");
                          formikProps.form.setFieldValue("metadata.organizations", []);
                          this.setState({
                            organizationsKey: `cleared-${Date.now()}`,
                            organizationSuggestions: [],
                          });
                        }
                      }}
                      noQueryMessage={i18next.t("Search for project...")}
                      clearable
                      allowAdditions={false}
                      multiple={false}
                      label={
                        <FieldLabel
                          htmlFor="metadata.project_id"
                          icon="group"
                          label={i18next.t("Project")}
                        />
                      }
                      required
                    />
                    {hasCommunity && (
                      <SelectField
                        label={
                          <FieldLabel
                            icon="user"
                            label={i18next.t("Community")}
                            id="community-label"
                            class="block"
                          />
                        }
                        fieldPath="metadata.community"
                        options={communities}
                        defaultValue="Loading..."
                        required
                        placeholder="Select your community"
                      />
                    )}
                    {!hasCommunity && (
                      <>
                        {values.metadata.project_id && (
                          <Message info size="tiny" className="rel-mt-1 rel-mb-1">
                            <Icon name="magic" />
                            {i18next.t(
                              "Some fields below have been auto-filled from the selected project. Please review them before creating the community."
                            )}
                          </Message>
                        )}
                        <TextField
                          required
                          id="metadata.title"
                          fluid
                          fieldPath="metadata.title"
                          // Prevent submitting before the value is updated:
                          onKeyDown={(e) => {
                            e.key === "Enter" && e.preventDefault();
                          }}
                          label={
                            <FieldLabel
                              htmlFor="metadata.title"
                              icon="book"
                              label={i18next.t("Community name")}
                            />
                          }
                        />
                        <TextField
                          required
                          id="metadata.slug"
                          fluid
                          fieldPath="metadata.slug"
                          className="text-muted"
                          onKeyDown={(e) => {
                            e.key === "Enter" && e.preventDefault();
                          }}
                          helpText={
                            <>
                              {i18next.t(
                                "This is your community's unique identifier. You will be able to access your community through the URL:"
                              )}
                              <br />
                              {`${formConfig.SITE_UI_URL}/communities/${values.metadata.slug}`}
                            </>
                          }
                          label={
                            <FieldLabel
                              htmlFor="metadata.slug"
                              icon="barcode"
                              label={i18next.t("Identifier")}
                            />
                          }
                        />
                        <TextAreaField
                          rows={4}
                          id="metadata.description"
                          fieldPath="metadata.description"
                          label={
                            <FieldLabel
                              htmlFor="metadata.description"
                              icon="pencil alternate"
                              label={
                                <>
                                  {i18next.t("Short description")}
                                  {autoFilledHint}
                                </>
                              }
                            />
                          }
                        />
                        <TextField
                          id="metadata.website"
                          fluid
                          fieldPath="metadata.website"
                          label={
                            <FieldLabel
                              htmlFor="metadata.website"
                              icon="linkify"
                              label={
                                <>
                                  {i18next.t("Website")}
                                  {autoFilledHint}
                                </>
                              }
                            />
                          }
                        />
                        <RemoteSelectField
                          key={organizationsKey}
                          fieldPath="metadata.organizations"
                          suggestionAPIUrl="/api/affiliations"
                          suggestionAPIHeaders={{
                            Accept: "application/vnd.inveniordm.v1+json",
                          }}
                          placeholder={i18next.t("Search for an organization by name")}
                          clearable
                          multiple
                          initialSuggestions={organizationSuggestions}
                          serializeSuggestions={(orgs) => {
                            orgs.forEach((org) => {
                              if (org.id && !this.knownOrganizations[org.id]) {
                                this.knownOrganizations[org.id] = org.name;
                              }
                            });
                            return AffiliationsSuggestions(orgs, true);
                          }}
                          label={
                            <FieldLabel
                              htmlFor="metadata.organizations"
                              icon="group"
                              label={
                                <>
                                  {i18next.t("Organizations")}
                                  {organizationSuggestions.length > 0 && autoFilledHint}
                                </>
                              }
                            />
                          }
                          noQueryMessage={i18next.t("Search for organizations...")}
                          additionLabel={i18next.t("Add organization: ")}
                          allowAdditions
                          search={(filteredOptions) => filteredOptions}
                        />
                        <Message info size="tiny" className="rel-mt-1">
                          <Icon name="info circle" />
                          {i18next.t(
                            "These organizations are automatically added based on the project's consortium. You can manage organization membership after the community is created."
                          )}
                        </Message>
                      </>
                    )}
                    {canCreateRestricted && (
                      <>
                        <Header as="h3">{i18next.t("Community visibility")}</Header>
                        {formConfig.access.visibility.map((item) => (
                          <React.Fragment key={item.value}>
                            <RadioField
                              key={item.value}
                              fieldPath="access.visibility"
                              label={item.text}
                              labelIcon={item.icon}
                              checked={_get(values, "access.visibility") === item.value}
                              value={item.value}
                              onChange={({ event, data, formikProps }) => {
                                formikProps.form.setFieldValue(
                                  "access.visibility",
                                  item.value
                                );
                              }}
                            />
                            <label className="helptext">{item.helpText}</label>
                          </React.Fragment>
                        ))}
                      </>
                    )}
                  </Grid.Column>
                </Grid.Row>
                <Grid.Row>
                  <Grid.Column textAlign="center">
                    <Button
                      positive
                      icon
                      labelPosition="left"
                      loading={isSubmitting}
                      disabled={isSubmitting}
                      type="button"
                      onClick={(event) => handleSubmit(event)}
                    >
                      <Icon name="plus" />
                      {hasCommunity
                        ? i18next.t("Create request")
                        : i18next.t("Create community")}
                    </Button>
                  </Grid.Column>
                </Grid.Row>
              </Grid>
            </Form>
          );
        }}
      </Formik>
    );
  }
}

SubcommunityCreateForm.propTypes = {
  formConfig: PropTypes.object.isRequired,
  canCreateRestricted: PropTypes.bool.isRequired,
  community: PropTypes.string.isRequired,
};

export default SubcommunityCreateForm;
