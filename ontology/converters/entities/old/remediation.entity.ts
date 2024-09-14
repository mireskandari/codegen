import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvChildEntity, VsolvEntity } from '@vsolv/dev-kit/nest';
import { ReimbursementEntity } from '@vsolv/packages/reimbursement/api';
import { Claim } from '@wsphere/warranties/domain';
import {
  Column,
  CreateDateColumn,
  JoinColumn,
  OneToOne,
  PrimaryColumn,
  TableInheritance,
  UpdateDateColumn,
} from 'typeorm';
import { ClaimEntity } from '..';
import { ClaimRemediationAggregate, ClaimRemediationServiceReimbursementAggregate } from '../models';

@TableInheritance({ column: { name: 'type' } })
@VsolvEntity({ name: 'claim_remediation' }, 'tenant')
export abstract class ClaimRemediationEntity<T extends string> implements Claim.ClaimRemediation<T> {
  @PrimaryColumn()
  id!: string;

  @OneToOne(() => ClaimEntity, claim => claim.remediation)
  claim?: ClaimEntity;

  @CreateDateColumn()
  created!: Date;

  @UpdateDateColumn()
  modified!: Date;

  @Column()
  type!: T;

  @Column({ type: 'simple-enum', enum: Claim.RemediationStatus })
  status!: Claim.RemediationStatus;

  abstract toAggregate(publisher?: EventPublisher): ClaimRemediationAggregate<T>;
}

@VsolvChildEntity(undefined, 'tenant')
export class ClaimRemediationServiceReimbursementEntity extends ClaimRemediationEntity<'service-reimbursement'> {
  @Column({ nullable: true })
  fileName!: string | null;

  @Column({ nullable: true })
  reimbursementId!: string | null;

  @JoinColumn({ name: 'reimbursementId' })
  @OneToOne(() => ReimbursementEntity)
  reimbursement?: ReimbursementEntity;

  toAggregate(publisher?: EventPublisher): ClaimRemediationServiceReimbursementAggregate {
    return mergeObjectContext(
      new ClaimRemediationServiceReimbursementAggregate({
        reimbursement: this.reimbursement === null ? null : this.reimbursement?.toAggregate(publisher) ?? undefined,
        reimbursementId: this.reimbursementId,

        modified: this.modified,
        created: this.created,
        status: this.status,

        id: this.id,
      }),
      publisher
    );
  }
}
