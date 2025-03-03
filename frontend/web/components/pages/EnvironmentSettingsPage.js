import React, { Component } from 'react'
import ConfirmRemoveEnvironment from 'components/modals/ConfirmRemoveEnvironment'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import withWebhooks from 'common/providers/withWebhooks'
import CreateWebhookModal from 'components/modals/CreateWebhook'
import ConfirmRemoveWebhook from 'components/modals/ConfirmRemoveWebhook'
import ConfirmToggleEnvFeature from 'components/modals/ConfirmToggleEnvFeature'
import EditPermissions from 'components/EditPermissions'
import ServerSideSDKKeys from 'components/ServerSideSDKKeys'
import PaymentModal from 'components/modals/Payment'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import JSONReference from 'components/JSONReference'
import ColourSelect from 'components/tags/ColourSelect'
import Constants from 'common/constants'
import Switch from 'components/Switch'

const showDisabledFlagOptions = [
  { label: 'Inherit from Project', value: null },
  { label: 'Disabled', value: false },
  { label: 'Enabled', value: true },
]

const EnvironmentSettingsPage = class extends Component {
  static displayName = 'EnvironmentSettingsPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {}
    AppActions.getProject(this.props.match.params.projectId)
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.ENVIRONMENT_SETTINGS)
    this.props.getWebhooks()
  }

  onSave = () => {
    toast('Environment Saved')
  }

  componentDidUpdate(prevProps) {
    if (
      this.props.match.params.projectId !== prevProps.match.params.projectId
    ) {
      AppActions.getProject(this.props.match.params.projectId)
    }
  }

  onRemove = () => {
    toast('Your project has been removed')
    this.context.router.history.replace('/projects')
  }

  confirmRemove = (environment, cb) => {
    openModal(
      'Remove Environment',
      <ConfirmRemoveEnvironment environment={environment} cb={cb} />,
      'p-0',
    )
  }

  onRemoveEnvironment = () => {
    const envs = ProjectStore.getEnvs()
    if (envs && envs.length) {
      this.context.router.history.replace(
        `/project/${this.props.match.params.projectId}/environment` +
          `/${envs[0].api_key}/features`,
      )
    } else {
      this.context.router.history.replace(
        `/project/${this.props.match.params.projectId}/environment/create`,
      )
    }
  }

  saveEnv = (e) => {
    e && e.preventDefault()
    const { description, name } = this.state
    if (ProjectStore.isSaving || !name) {
      return
    }
    const has4EyesPermission = Utils.getPlansPermission('4_EYES')

    const env = _.find(ProjectStore.getEnvs(), {
      api_key: this.props.match.params.environmentId,
    })
    AppActions.editEnv(
      Object.assign({}, env, {
        allow_client_traits: !!this.state.allow_client_traits,
        banner_colour: this.state.banner_colour,
        banner_text: this.state.banner_text,
        description: description || env.description,
        hide_disabled_flags: this.state.hide_disabled_flags,
        hide_sensitive_data: !!this.state.hide_sensitive_data,
        minimum_change_request_approvals: has4EyesPermission
          ? this.state.minimum_change_request_approvals
          : null,
        name: name || env.name,
        use_identity_composite_key_for_hashing:
          !!this.state.use_identity_composite_key_for_hashing,
      }),
    )
  }

  saveDisabled = () => {
    const { name } = this.state
    if (ProjectStore.isSaving || !name) {
      return true
    }

    // Must have name
    return !name
  }

  createWebhook = () => {
    openModal(
      'New Webhook',
      <CreateWebhookModal
        router={this.context.router}
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        save={this.props.createWebhook}
      />,
    )
  }

  editWebhook = (webhook) => {
    openModal(
      'Edit Webhook',
      <CreateWebhookModal
        router={this.context.router}
        webhook={webhook}
        isEdit
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        save={this.props.saveWebhook}
      />,
    )
  }

  deleteWebhook = (webhook) => {
    openModal(
      'Remove Webhook',
      <ConfirmRemoveWebhook
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        url={webhook.url}
        cb={() => this.props.deleteWebhook(webhook)}
      />,
      'p-0',
    )
  }

  confirmToggle = (description, feature, featureValue) => {
    openModal(
      'Enable "Hide Sensitive Data"',
      <ConfirmToggleEnvFeature
        description={description}
        feature={feature}
        featureValue={featureValue}
        onToggleChange={(value) => {
          this.setState({ hide_sensitive_data: value }, this.saveEnv)
          closeModal()
        }}
      />,
    )
  }

  render() {
    const {
      props: { webhooks, webhooksLoading },
      state: {
        allow_client_traits,
        hide_sensitive_data,
        name,
        use_identity_composite_key_for_hashing,
      },
    } = this
    const has4EyesPermission = Utils.getPlansPermission('4_EYES')

    return (
      <div className='app-container'>
        <ProjectProvider
          onRemoveEnvironment={this.onRemoveEnvironment}
          id={this.props.match.params.projectId}
          onRemove={this.onRemove}
          onSave={this.onSave}
        >
          {({ deleteEnv, isLoading, isSaving, project }) => {
            const env = _.find(project.environments, {
              api_key: this.props.match.params.environmentId,
            })
            if (
              env &&
              typeof this.state.minimum_change_request_approvals === 'undefined'
            ) {
              setTimeout(() => {
                this.setState({
                  allow_client_traits: !!env.allow_client_traits,
                  banner_colour: env.banner_colour || Constants.tagColors[0],
                  banner_text: env.banner_text,
                  hide_disabled_flags: env.hide_disabled_flags,
                  hide_sensitive_data: !!env.hide_sensitive_data,
                  minimum_change_request_approvals: Utils.changeRequestsEnabled(
                    env.minimum_change_request_approvals,
                  )
                    ? env.minimum_change_request_approvals
                    : null,
                  name: env.name,
                  use_identity_composite_key_for_hashing:
                    !!env.use_identity_composite_key_for_hashing,
                })
              }, 10)
            }
            return (
              <div className='container'>
                {isLoading && (
                  <div className='centered-container'>
                    <Loader />
                  </div>
                )}
                {!isLoading && (
                  <Tabs uncontrolled>
                    <TabItem tabLabel='General'>
                      <div className='mt-4'>
                        <JSONReference title={'Environment'} json={env} />
                        <div>
                          <form onSubmit={this.saveEnv}>
                            <div className='row'>
                              <div className='col-md-6'>
                                <InputGroup
                                  ref={(e) => (this.input = e)}
                                  value={
                                    typeof this.state.name === 'string'
                                      ? this.state.name
                                      : env.name
                                  }
                                  inputProps={{
                                    className: 'full-width',
                                    name: 'env-name',
                                  }}
                                  className='full-width'
                                  onChange={(e) =>
                                    this.setState({
                                      name: Utils.safeParseEventValue(e),
                                    })
                                  }
                                  isValid={name && name.length}
                                  type='text'
                                  title='Environment Name'
                                  placeholder='Environment Name'
                                />
                              </div>
                            </div>
                            <div className='row'>
                              <div className='col-md-6'>
                                <InputGroup
                                  textarea
                                  ref={(e) => (this.input = e)}
                                  value={
                                    typeof this.state.description === 'string'
                                      ? this.state.description
                                      : env.description
                                  }
                                  inputProps={{
                                    className: 'input--wide textarea-lg',
                                  }}
                                  onChange={(e) =>
                                    this.setState({
                                      description: Utils.safeParseEventValue(e),
                                    })
                                  }
                                  isValid={name && name.length}
                                  type='text'
                                  title='Environment Description'
                                  placeholder='Environment Description'
                                />
                              </div>
                            </div>
                            <div className='row'>
                              <div className='col-md-6 text-right'>
                                <Button
                                  id='save-env-btn'
                                  className='float-right mb-4'
                                  type='submit'
                                  disabled={this.saveDisabled()}
                                >
                                  {isSaving ? 'Updating' : 'Update'}
                                </Button>
                              </div>
                            </div>
                          </form>
                        </div>
                        <div>
                          <Row space>
                            <div className='col-md-8 pl-0'>
                              <h5 className='m-b-0'>Environment Banner</h5>
                              <p className='fs-small lh-sm mb-0'>
                                This will show a banner whenever you view its
                                pages, this is generally used to warn people
                                that they are viewing and editing a sensitive
                                environment.
                              </p>
                            </div>
                            <Switch
                              onChange={(value) =>
                                this.setState(
                                  {
                                    banner_text: value
                                      ? `${env.name} Environment`
                                      : null,
                                  },
                                  this.saveEnv,
                                )
                              }
                              checked={
                                typeof this.state.banner_text === 'string'
                              }
                            />
                          </Row>
                          {typeof this.state.banner_text === 'string' && (
                            <Row className='mt-2'>
                              <Input
                                style={{ width: 400 }}
                                placeholder='Banner text'
                                value={this.state.banner_text}
                                onChange={(e) =>
                                  this.setState({
                                    banner_text: Utils.safeParseEventValue(e),
                                  })
                                }
                              />
                              <div className='ml-2'>
                                <ColourSelect
                                  value={this.state.banner_colour}
                                  onChange={(banner_colour) =>
                                    this.setState({ banner_colour })
                                  }
                                />
                              </div>
                              <Button
                                onClick={this.saveEnv}
                                className='ml-2'
                                size='small'
                              >
                                Save
                              </Button>
                            </Row>
                          )}
                        </div>
                        {Utils.getFlagsmithHasFeature(
                          'configure_hide_sensitive_data',
                        ) && (
                          <div>
                            <Row space style={{ marginTop: '1.5rem' }}>
                              <div className='col-md-8 pl-0'>
                                <h5 className='m-b-0'>Hide sensitive data</h5>
                                <p className='fs-small lh-sm'>
                                  Exclude sensitive data from endpoints
                                  returning flags and identity information to
                                  the SDKs or via our REST API. For full
                                  information on the excluded fields see
                                  documentation{' '}
                                  <Button
                                    theme='text'
                                    href='https://docs.flagsmith.com/system-administration/security#hide-sensitive-data'
                                    target='_blank'
                                  >
                                    here.
                                  </Button>
                                  <br />
                                  <strong>
                                    Warning! Enabling this feature will change
                                    the response from the API and could break
                                    your existing code.
                                  </strong>
                                </p>
                              </div>
                              <div className='col-md-4 pr-0 text-right'>
                                <div>
                                  <Switch
                                    className='float-right'
                                    checked={hide_sensitive_data}
                                    onChange={(v) => {
                                      this.confirmToggle(
                                        'The data returned from the API will change and could break your existing code. Are you sure that you want to change this value?',
                                        'hide_sensitive_data',
                                        hide_sensitive_data,
                                      )
                                    }}
                                  />
                                </div>
                              </div>
                            </Row>
                          </div>
                        )}
                        <FormGroup className='mt-4'>
                          <Row space>
                            <div className='col-md-8 pl-0'>
                              <h5 className='m-b-0'>Change Requests</h5>
                              {!has4EyesPermission ? (
                                <p className='fs-small lh-sm'>
                                  View and manage your feature changes with a
                                  Change Request flow with our{' '}
                                  <Button
                                    theme='text'
                                    onClick={() => {
                                      openModal(
                                        'Payment plans',
                                        <PaymentModal viewOnly={false} />,
                                        'modal-lg',
                                      )
                                    }}
                                  >
                                    Scale-up plan
                                  </Button>
                                  . Find out more{' '}
                                  <Button
                                    theme='text'
                                    href='https://docs.flagsmith.com/advanced-use/change-requests'
                                    target='_blank'
                                  >
                                    here
                                  </Button>
                                  .
                                </p>
                              ) : (
                                <p className='fs-small lh-sm'>
                                  Require a minimum number of people to approve
                                  changes to features.{' '}
                                  <Button
                                    theme='text'
                                    href='https://docs.flagsmith.com/advanced-use/change-requests'
                                    target='_blank'
                                  >
                                    Learn about Change Requests.
                                  </Button>
                                </p>
                              )}
                            </div>
                            <div className='col-md-4 pr-0 text-right'>
                              <div>
                                <Switch
                                  disabled={!has4EyesPermission}
                                  className='float-right'
                                  checked={
                                    has4EyesPermission &&
                                    Utils.changeRequestsEnabled(
                                      this.state
                                        .minimum_change_request_approvals,
                                    )
                                  }
                                  onChange={(v) =>
                                    this.setState(
                                      {
                                        minimum_change_request_approvals: v
                                          ? 0
                                          : null,
                                      },
                                      this.saveEnv,
                                    )
                                  }
                                />
                              </div>
                            </div>
                          </Row>

                          {Utils.changeRequestsEnabled(
                            this.state.minimum_change_request_approvals,
                          ) &&
                            has4EyesPermission && (
                              <div>
                                <div className='mb-2'>
                                  <strong>Minimum number of approvals</strong>
                                </div>
                                <Row>
                                  <Column className='m-l-0'>
                                    <Input
                                      ref={(e) => (this.input = e)}
                                      value={`${this.state.minimum_change_request_approvals}`}
                                      inputClassName='input input--wide'
                                      name='env-name'
                                      min={0}
                                      style={{ minWidth: 50 }}
                                      onChange={(e) => {
                                        if (!Utils.safeParseEventValue(e))
                                          return
                                        this.setState({
                                          minimum_change_request_approvals:
                                            parseInt(
                                              Utils.safeParseEventValue(e),
                                            ),
                                        })
                                      }}
                                      isValid={name && name.length}
                                      type='number'
                                      placeholder='Minimum number of approvals'
                                    />
                                  </Column>
                                  <Button
                                    type='button'
                                    onClick={this.saveEnv}
                                    id='save-env-btn'
                                    className='float-right'
                                    disabled={
                                      this.saveDisabled() ||
                                      isSaving ||
                                      isLoading
                                    }
                                  >
                                    {isSaving || isLoading ? 'Saving' : 'Save'}
                                  </Button>
                                </Row>
                              </div>
                            )}
                        </FormGroup>
                        <FormGroup className='mt-4'>
                          <Row className='mt-4' space>
                            <div className='col-md-8 pl-0'>
                              <h5>Delete Environment</h5>
                              <p className='fs-small lh-sm'>
                                This environment will be permanently deleted.
                              </p>
                            </div>
                            <Button
                              id='delete-env-btn'
                              onClick={() =>
                                this.confirmRemove(
                                  _.find(project.environments, {
                                    api_key:
                                      this.props.match.params.environmentId,
                                  }),
                                  () => {
                                    deleteEnv(
                                      _.find(project.environments, {
                                        api_key:
                                          this.props.match.params.environmentId,
                                      }),
                                    )
                                  },
                                )
                              }
                              className='btn btn--with-icon ml-auto btn--remove'
                            >
                              <RemoveIcon />
                            </Button>
                          </Row>
                        </FormGroup>
                      </div>
                    </TabItem>
                    <TabItem
                      data-test='js-sdk-settings'
                      tabLabel='SDK Settings'
                    >
                      <div className='mt-4'>
                        <JSONReference title={'Environment'} json={env} />
                        <div>
                          <form onSubmit={this.saveEnv}>
                            {Utils.getFlagsmithHasFeature(
                              'hide_disabled_flags_environment',
                            ) && (
                              <Row className='mb-4' space>
                                <div className='col-md-8 pl-0'>
                                  <h5 className='m-b-0'>
                                    Hide disabled flags from SDKs
                                  </h5>
                                  <p className='mb-0  fs-small lh-sm'>
                                    To prevent letting your users know about
                                    your upcoming features and to cut down on
                                    payload, enabling this will prevent the API
                                    from returning features that are disabled.
                                    You can also manage this in{' '}
                                    <Link
                                      to={`/project/${this.props.match.params.projectId}/settings`}
                                    >
                                      Project settings
                                    </Link>
                                    .
                                  </p>
                                </div>
                                <div className='col-md-3'>
                                  <Select
                                    value={
                                      showDisabledFlagOptions.find(
                                        (v) =>
                                          v.value ===
                                          this.state.hide_disabled_flags,
                                      ) || showDisabledFlagOptions[0]
                                    }
                                    onChange={(v) => {
                                      this.setState(
                                        { hide_disabled_flags: v.value },
                                        this.saveEnv,
                                      )
                                    }}
                                    options={showDisabledFlagOptions}
                                    data-test='js-hide-disabled-flags'
                                    disabled={isSaving}
                                  />
                                </div>
                              </Row>
                            )}
                            <Row className='mt-4' space>
                              <div className='col-md-8 pl-0'>
                                <h5 className='m-b-0'>
                                  Allow client SDKs to set user traits
                                </h5>
                                <p className='fs-small lh-sm'>
                                  Disabling this option will prevent client SDKs
                                  from using the client key from setting traits.
                                </p>
                              </div>
                              <div className='col-md-4 pr-0 text-right'>
                                <div>
                                  <Switch
                                    className='float-right'
                                    checked={allow_client_traits}
                                    onChange={(v) => {
                                      this.setState(
                                        { allow_client_traits: v },
                                        this.saveEnv,
                                      )
                                    }}
                                  />
                                </div>
                              </div>
                              {Utils.getFlagsmithHasFeature(
                                'consistent_hashing_setting',
                              ) && (
                                <>
                                  <Row className='mt-4' space>
                                    <div className='col-md-8 pl-0'>
                                      <h5 className='m-b-0'>
                                        Use Consistent Hashing
                                      </h5>
                                      <p className='fs-small lh-sm'>
                                        Enabling this setting will ensure that
                                        multivariate and percentage split
                                        evaluations made by the API are
                                        consistent with those made by local
                                        evaluation mode in our server side SDKs.
                                      </p>
                                    </div>
                                    <div className='col-md-4 pr-0 text-right'>
                                      <div>
                                        <Switch
                                          className='float-right'
                                          checked={
                                            use_identity_composite_key_for_hashing
                                          }
                                          onChange={(v) => {
                                            this.setState(
                                              {
                                                use_identity_composite_key_for_hashing:
                                                  v,
                                              },
                                              this.saveEnv,
                                            )
                                          }}
                                        />
                                      </div>
                                    </div>
                                  </Row>
                                  <p className='text-danger  fs-small lh-sm'>
                                    Warning: Toggling this setting will mean
                                    that some users will start receiving
                                    different values for multivariate flags and
                                    flags with a percentage split segment
                                    override via the API / remote evaluation.
                                    Values received in local evaluation mode
                                    will not change.
                                  </p>
                                </>
                              )}
                            </Row>
                          </form>
                        </div>
                      </div>
                    </TabItem>
                    <TabItem tabLabel='Keys'>
                      <FormGroup className='mt-4'>
                        <h5>Client-side Environment Key</h5>
                        <div className='row'>
                          <div className='col-md-6'>
                            <Row>
                              <Flex>
                                <Input
                                  value={this.props.match.params.environmentId}
                                  inputClassName='input input--wide'
                                  type='text'
                                  title={<h3>Client-side Environment Key</h3>}
                                  placeholder='Client-side Environment Key'
                                />
                              </Flex>
                              <Button
                                onClick={() => {
                                  navigator.clipboard.writeText(
                                    this.props.match.params.environmentId,
                                  )
                                  toast('Copied')
                                }}
                                className='ml-2'
                              >
                                Copy
                              </Button>
                            </Row>
                          </div>
                        </div>
                      </FormGroup>
                      <ServerSideSDKKeys
                        environmentId={this.props.match.params.environmentId}
                      />
                    </TabItem>
                    <TabItem tabLabel='Members'>
                      <FormGroup>
                        <EditPermissions
                          tabClassName='flat-panel'
                          parentId={this.props.match.params.projectId}
                          parentLevel='project'
                          parentSettingsLink={`/project/${this.props.match.params.projectId}/settings`}
                          id={this.props.match.params.environmentId}
                          router={this.context.router}
                          level='environment'
                        />
                      </FormGroup>
                    </TabItem>
                    <TabItem tabLabel='Webhooks'>
                      <FormGroup className='mt-4'>
                        <Row className='mb-3' space>
                          <div className='col-md-8 pl-0'>
                            <h5 className='m-b-0'>Feature Webhooks</h5>
                            <p className='fs-small lh-sm'>
                              Feature webhooks let you know when features have
                              changed. You can configure 1 or more Feature
                              Webhooks per Environment.{' '}
                              <Button
                                theme='text'
                                href='https://docs.flagsmith.com/system-administration/webhooks#environment-web-hooks'
                                target='_blank'
                              >
                                Learn about Feature Webhooks.
                              </Button>
                            </p>
                          </div>
                          <div className='col-md-4 pr-0'>
                            <Button
                              className='float-right'
                              onClick={this.createWebhook}
                            >
                              Create feature webhook
                            </Button>
                          </div>
                        </Row>
                        {webhooksLoading && !webhooks ? (
                          <Loader />
                        ) : (
                          <PanelSearch
                            id='webhook-list'
                            title={
                              <Tooltip
                                title={
                                  <h6 className='mb-0'>
                                    Webhooks{' '}
                                    <span className='icon ion-ios-information-circle' />
                                  </h6>
                                }
                                place='right'
                              >
                                {Constants.strings.WEBHOOKS_DESCRIPTION}
                              </Tooltip>
                            }
                            className='no-pad'
                            icon='ion-md-cloud'
                            items={webhooks}
                            renderRow={(webhook) => (
                              <Row
                                onClick={() => {
                                  this.editWebhook(webhook)
                                }}
                                space
                                className='list-item clickable cursor-pointer'
                                key={webhook.id}
                              >
                                <div>
                                  <Button theme='text'>{webhook.url}</Button>
                                  <div className='list-item-footer faint'>
                                    Created{' '}
                                    {moment(webhook.created_date).format(
                                      'DD/MMM/YYYY',
                                    )}
                                  </div>
                                </div>
                                <Row>
                                  <Switch checked={webhook.enabled} />
                                  <button
                                    id='delete-invite'
                                    type='button'
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      e.preventDefault()
                                      this.deleteWebhook(webhook)
                                    }}
                                    className='btn btn--with-icon ml-auto btn--remove'
                                  >
                                    <RemoveIcon />
                                  </button>
                                </Row>
                              </Row>
                            )}
                            renderNoResults={
                              <Panel
                                id='users-list'
                                icon='ion-md-cloud'
                                className='fs-small lh-sm'
                                title={
                                  <Tooltip
                                    title={
                                      <h6 className='mb-0'>
                                        Webhooks{' '}
                                        <span className='icon ion-ios-information-circle' />
                                      </h6>
                                    }
                                    place='right'
                                  >
                                    {Constants.strings.WEBHOOKS_DESCRIPTION}
                                  </Tooltip>
                                }
                              >
                                You currently have no Feature Webhooks
                                configured for this Environment.
                              </Panel>
                            }
                            isLoading={this.props.webhookLoading}
                          />
                        )}
                      </FormGroup>
                    </TabItem>
                  </Tabs>
                )}
              </div>
            )
          }}
        </ProjectProvider>
      </div>
    )
  }
}

EnvironmentSettingsPage.propTypes = {}

module.exports = ConfigProvider(withWebhooks(EnvironmentSettingsPage))
