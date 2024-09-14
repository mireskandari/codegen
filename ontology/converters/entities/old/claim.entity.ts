/* eslint-disable @typescript-eslint/no-non-null-assertion */
import { EventPublisher } from '@nestjs/cqrs';
import { MultiTenantConnectionManager } from '@vsolv/core/multi-tenant/api';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Claim } from '@wsphere/warranties/domain';
import {
  Column,
  CreateDateColumn,
  JoinColumn,
  ManyToOne,
  OneToMany,
  OneToOne,
  PrimaryColumn,
  UpdateDateColumn,
} from 'typeorm';
import { CoverageEntity } from '../../coverage';
import { ClaimEvidenceEntity } from '../../evidence';
import { WarrantyEntity } from '../../warranty';
import { ClaimActivityAggregate, ClaimAggregate } from '../models';
import { ClaimRemediationEntity } from './remediation.entity';

@VsolvEntity({ name: 'claim_activity' }, 'tenant')
export class ClaimActivityEntity {
  @PrimaryColumn()
  id!: string;

  @ManyToOne(() => ClaimEntity)
  @JoinColumn({ name: 'claimId' })
  claim?: string;

  @Column()
  claimId!: string;

  @Column()
  icon!: string;

  @Column()
  title!: string;

  @Column()
  message!: string;

  @CreateDateColumn()
  created!: Date;

  toAggregate(publisher?: EventPublisher) {
    return mergeObjectContext(
      new ClaimActivityAggregate({
        id: this.id,
        claimId: this.claimId,
        message: this.message,
        created: this.created,
        title: this.title,
        icon: this.icon,
      }),
      publisher
    );
  }
}

@VsolvEntity({ name: 'claim' }, 'tenant')
export class ClaimEntity {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true })
  referenceId!: string | null;

  @CreateDateColumn()
  created!: Date;

  @UpdateDateColumn()
  modified!: Date;

  @Column()
  details!: string;

  @Column({ type: 'simple-enum', enum: Claim.Status })
  status!: Claim.Status;

  @Column()
  warrantyId!: string;

  @JoinColumn({ name: 'warrantyId' })
  @ManyToOne(() => WarrantyEntity)
  warranty?: WarrantyEntity<string>;

  @Column()
  affectedCoverageId!: string;

  @JoinColumn({ name: 'affectedCoverageId' })
  @ManyToOne(() => CoverageEntity)
  affectedCoverage?: CoverageEntity;

  @OneToMany(() => ClaimEvidenceEntity, ev => ev.claim)
  evidence?: ClaimEvidenceEntity[];

  @Column({ nullable: true })
  liabilityAmount!: number | null;

  @Column({ nullable: true })
  remediationId!: string | null;

  @JoinColumn({ name: 'remediationId' })
  @OneToOne(() => ClaimRemediationEntity, rem => rem.claim, { nullable: true })
  remediation?: ClaimRemediationEntity<string>;

  @OneToMany(() => ClaimActivityEntity, act => act.claim)
  activity?: ClaimActivityEntity[];

  toAggregate(publisher?: EventPublisher) {
    return mergeObjectContext(
      new ClaimAggregate({
        id: this.id,
        referenceId: this.referenceId,

        created: this.created,
        modified: this.modified,

        status: this.status,

        details: this.details,
        liabilityAmount: this.liabilityAmount,

        warrantyId: this.warrantyId,
        warranty: this.warranty?.toAggregate(publisher) ?? undefined,

        affectedCoverageId: this.affectedCoverageId,
        affectedCoverage: this.affectedCoverage?.toAggregate(publisher) ?? undefined,

        evidence: this.evidence?.map(evd => evd.toAggregate(publisher)) ?? undefined,

        remediationId: this.remediationId,
        remediation: this.remediation?.toAggregate(publisher) ?? undefined,

        activity: this.activity?.map(act => act.toAggregate(publisher)) ?? undefined,
      }),
      publisher
    );
  }

  static async getClaims(
    warrantyId: string,
    tenantId: string,
    connectionManager: MultiTenantConnectionManager,
    publisher?: EventPublisher
  ): Promise<ClaimAggregate[]> {
    const repo = await connectionManager.getRepository(ClaimEntity, tenantId);
    if (!repo) throw new Error('Unable to establish database connection');

    const entities = await repo.find({ where: { warrantyId } });
    return entities.map(entity => entity.toAggregate(publisher));
  }

  static async getClaim(
    claimId: string,
    tenantId: string,
    connectionManager: MultiTenantConnectionManager,
    publisher?: EventPublisher
  ): Promise<ClaimAggregate> {
    const repo = await connectionManager.getRepository(ClaimEntity, tenantId);
    if (!repo) throw new Error('Unable to establish database connection');

    const entity = await repo.findOneOrFail({ where: { id: claimId }, relations: ['affectedCoverage', 'remediation'] });
    return entity.toAggregate(publisher);
  }
}
